#!/usr/bin/env python3

from . import liblsdj
from . import env
from .auth import Auth
from .store import Store
from .flask import Flask
from .models import Models

from flask import request, redirect, url_for, render_template, flash, g
from flask_bcrypt import Bcrypt
from redis import Redis
from werkzeug import exceptions
from werkzeug.utils import secure_filename

from pathlib import Path

app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
)

bcrypt = Bcrypt(app)

redis = Redis(
    decode_responses=True,
    **env.redis_config(),
)

store = Store(**env.store_config())

auth = Auth(redis=redis, bcrypt=bcrypt, **env.auth_config())

models = Models(store)

# TODO this should somehow be elsewhere
@app.template_filter('as_bytes')
def as_bytes(x: int) -> str:
    s = str(x)
    digits = len(s)

    if digits < 4:
        return f'{x} B'

    split = (digits - 1) % 3 + 1
    prefix = 'kMGTEPEZY'[(digits - 4) // 3]
    return f'{s[:split]}.{s[split:3]}'.rstrip('.') + f' {prefix}B'

@app.after_request
def security_headers(response):
    response.headers['Content-Security-Policy'] = '''default-src 'none'; style-src 'self';'''
    response.headers['X-Frame-Options'] = 'deny'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

@app.route('/ok')
def ok():
    return 'ok'

@app.route('/')
def root():
    return render_template('root.html', auth=auth)

@app.route('/login', methods=('GET', 'POST'))
@auth.login_form(success_redirect='root')
def login():
    return render_template('login.html', auth=auth)

@app.route('/signup', methods=('GET', 'POST'))
@app.route('/signup/<rid>', methods=('GET',))
@auth.signup_form(success_redirect='root')
def signup(rid=None):
    return render_template('signup.html', auth=auth, rid=rid)

@app.route('/referrals', methods=('GET', 'POST'))
@auth.required()
def referrals():
    uid = session['u']
    context = dict()

    if request.method == 'POST':
        try:
            context['referral'] = rid = self.auth.generate_referral(uid)
            context['referral_url'] = url_for('signup', referral=rid)
        except AuthError:
            flash("You can't generate a referral right now.")

    referral_cooldown = self.redis.ttl(f'referral_cooldown:{uid}')
    if referral_cooldown >= 0:
        context['referral_cooldown'] = referral_cooldown + 1

    return render_template('referrals.html', auth=auth, **context)

@app.route('/logout')
def logout():
    auth.deauth()
    return redirect(url_for('root'))

@app.route('/srams', methods=('POST',))
@auth.required()
def sram_upload():
    if request.method == 'POST':
        if 'sram' not in request.files:
            raise exceptions.BadRequest("No SRAM file provided!")

        # temporarily save sram locally
        with store.stash(request.files['sram']) as f:

            # split into track files
            with liblsdj.split(f.name) as d:
                trackpaths = {secure_filename(p.name): str(p) for p in Path(d).iterdir()}

                # ensure all paths are free
                to_upload = list(store.new_files('track', trackpaths.keys()))
                for name in to_upload:
                    path = trackpaths[name]
                    store.put('track', path, name=name)

            # success! store sram in s3
            sram_name = store.put('sram', f.name)

            msg = f"{len(to_upload)} new tracks saved from SRAM file {sram_name}"
            if len(to_upload) < len(trackpaths):
                msg += f" ({len(trackpaths) - len(to_upload)} tracks existed already)"
            flash(msg)

        # TODO automatically make a playlist for each uploaded SRAM
        # TODO you should optionally be able to fix an old version of a track on a playlist
        return redirect(url_for('srams'))

@app.route('/srams')
#DEBUG @auth.required
def srams():
    return render_template('srams.html', auth=auth, srams=sorted(models.srams().items()), total_size=store.usage('sram'))

@app.route('/tracks')
#DEBUG @auth.required
def tracks():
    tracks = sorted(models.tracks().items())
    total_size = store.usage('track')
    return render_template('tracks.html', auth=auth, tracks=tracks, total_size=total_size)

@app.route('/tracks/<name>')
#DEBUG @auth.required
def track(name):
    # TODO wasteful
    track = models.tracks()[name]
    return render_template('track.html', auth=auth, name=name, track=track)

@app.route('/srams/<name>/download')
@auth.required()
def sram_download(name):
    return redirect(store.get_link('sram', name))

@app.route('/tracks/<name>/<int:version>/download')
@auth.required()
def track_download(name, version):
    name = models.tracks()[name]['versions'][version]['full_name']
    return redirect(store.get_link('track', name))

@app.route_delete('/srams/<name>', name="this SRAM file")
@auth.required()
def sram_delete(name):
    store.delete('sram', name)
    return redirect(url_for('srams'))

@app.route_delete('/tracks/<name>', name="all versions of this track")
@auth.required()
def track_delete(name):
    tracks = models.tracks()

    res = redirect(url_for('tracks') if len(tracks) > 1 else url_for('srams'))

    track = tracks[name]
    store.delete('track', [version['full_name'] for version in track['versions'].values()])

    return res

@app.route_delete('/tracks/<name>/<int:version>', name="this version of the track")
@auth.required()
def track_version_delete(name, version):
    tracks = models.tracks()
    track = tracks[name]
    version = track['versions'][version]

    res = redirect(url_for('track', name=name) if len(track['versions']) > 1 else url_for('tracks') if len(tracks) > 1 else url_for('srams'))

    store.delete('track', version['full_name'])
    return res

# DEBUG
@app.route_delete('/srams', name="all SRAM files")
@auth.required()
def srams_delete():
    store.delete('sram', list(store.items('sram').keys()))
    return redirect(url_for('srams'))

# DEBUG
@app.route_delete('/tracks', name="all versions of all tracks")
@auth.required()
def tracks_delete():
    store.delete('track', list(store.items('track').keys()))
    return redirect(url_for('tracks'))

# DEBUG
@app.route('/long')
def long():
    return render_template('long.html', auth=auth)
