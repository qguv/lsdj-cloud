#!/usr/bin/env python3

from . import liblsdj
from . import env
from .auth import Auth
from .store import Store
from .flask import Flask
from .s3_models import S3Models

from flask import request, redirect, url_for, render_template, flash, g, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from werkzeug import exceptions
from werkzeug.utils import secure_filename

from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse, parse_qs

app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    **env.flask_config(),
)

bcrypt = Bcrypt(app)

redis = Redis(
    decode_responses=True,
    **env.redis_config(),
)

store = Store(**env.store_config())

auth = Auth(redis=redis, bcrypt=bcrypt, **env.auth_config())

db = SQLAlchemy(app)

s3_models = S3Models(store)

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
    response.headers['Content-Security-Policy'] = '''default-src 'none'; script-src 'self'; style-src 'self';'''
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
@app.route('/signup/<uuid:rid>', methods=('GET',))
@auth.signup_form(success_redirect='root')
def signup(rid=None):
    context = dict()

    try:
        if rid:
            ruid = redis[f'referral:{rid}']
            context["ttl"] = timedelta(seconds=redis.ttl(f'referral:{rid}'))
            context["rhandle"] = redis.hget(f'user:{ruid}', 'handle')
    except KeyError:
        rid = None
        flash("That referral is not valid (anymore)")

    return render_template('signup.html', auth=auth, rid=rid, **context)

# TODO: URLs are wrong in the POST response but correct in the GET response
@app.route('/referrals', methods=('GET', 'POST'))
@auth.required()
def referrals():
    uid = session['u']
    context = dict()

    if request.method == 'POST':
        try:
            new_rid = auth.generate_referral(uid)
            flash("New referral generated!")
            return redirect(url_for('referrals', n=new_rid))
        except auth.AuthError:
            raise exceptions.TooManyRequests("You can't generate a referral right now.")

    prefix = 'referral:'
    context['referrals'] = sorted(
        (timedelta(seconds=redis.ttl(k)), k[len(prefix):])
        for k in redis.keys(prefix + '*')
        if redis.get(k) == session['u']
    )

    try:
        context["new_rid"] = parse_qs(urlparse(request.full_path).query)['n'][0]
    except KeyError:
        pass

    referral_cooldown = redis.ttl(f'referral_cooldown:{uid}')
    if referral_cooldown >= 0:
        context['referral_cooldown'] = timedelta(seconds=max(referral_cooldown, 1))

    return render_template('referrals.html', auth=auth, **context)

@app.route_delete('/referrals', auth, name="all referrals")
def referrals_delete():
    uid = session['u']
    prefix = 'referral:'

    referrals = [
        r
        for r in redis.keys(prefix + '*')
        if redis.get(r) == uid
    ]

    n = len(referrals)
    for referral in referrals:
        redis.delete(r)

    if n:
        flash(f"{n} referral{'' if n == 1 else 's'} deleted!")
    else:
        flash("No referrals to delete!")

    return redirect(url_for('referrals'))

@app.route_delete('/referrals/<uuid:name>', auth, name="this referral")
def referral_delete(name):
    ruid = redis.get(f'referral:{name}')
    if session['u'] != ruid:
        raise exceptions.Forbidden()

    redis.delete(f'referral:{name}')
    flash("Referral deleted.")
    return redirect(url_for('referrals'))

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
            try:
                with liblsdj.split(f.name) as d:
                    trackpaths = {secure_filename(p.name): str(p) for p in Path(d).iterdir()}

                    # ensure all paths are free
                    to_upload = list(store.new_files('track', trackpaths.keys()))
                    for name in to_upload:
                        path = trackpaths[name]
                        store.put('track', path, name=name)
            except liblsdj.CalledProcessError:
                flash("Couldn't process SRAM file; discarded!")
                return redirect(url_for('srams'))

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
    return render_template('srams.html', auth=auth, srams=sorted(s3_models.srams().items()), total_size=store.usage('sram'))

@app.route('/tracks')
#DEBUG @auth.required
def tracks():
    tracks = sorted(s3_models.tracks().items())
    total_size = store.usage('track')
    return render_template('tracks.html', auth=auth, tracks=tracks, total_size=total_size)

@app.route('/tracks/<name>')
#DEBUG @auth.required
def track(name):
    # TODO wasteful
    track = s3_models.tracks()[name]
    return render_template('track.html', auth=auth, name=name, track=track)

@app.route('/srams/<name>/download')
@auth.required()
def sram_download(name):
    return redirect(store.get_link('sram', name))

@app.route('/tracks/<name>/<int:version>/download')
@auth.required()
def track_download(name, version):
    name = s3_models.tracks()[name]['versions'][version]['full_name']
    return redirect(store.get_link('track', name))

@app.route_delete('/srams/<name>', auth, name="this SRAM file")
def sram_delete(name):
    store.delete('sram', name)
    flash(f"SRAM file {name} deleted.")
    return redirect(url_for('srams'))

@app.route_delete('/tracks/<name>', auth, name="all versions of this track")
def track_delete(name):
    tracks = s3_models.tracks()

    res = redirect(url_for('tracks') if len(tracks) > 1 else url_for('srams'))

    track = tracks[name]
    versions = [version['full_name'] for version in track['versions'].values()]
    n = len(versions)
    if n:
        store.delete('track', versions)

    if not n:
        flash(f"No versions of track {name} to delete!")
    if n == 1:
        flash(f"Deleted the only version of track {name}.")
    else:
        flash(f"All {n} versions of track {name} deleted.")

    return res

@app.route_delete('/tracks/<name>/<int:version>', auth, name="this version of the track")
def track_version_delete(name, version):
    tracks = s3_models.tracks()
    track = tracks[name]
    version = track['versions'][version]

    res = redirect(url_for('track', name=name) if len(track['versions']) > 1 else url_for('tracks') if len(tracks) > 1 else url_for('srams'))

    store.delete('track', version['full_name'])
    flash(f"Version {version} of track {name} deleted.")
    return res

# DEBUG
@app.route_delete('/srams', auth, name="all SRAM files")
def srams_delete():
    keys = list(store.items('sram').keys())
    n = len(keys)
    if n:
        store.delete('sram', keys)

    if not n:
        flash("No SRAM files to delete!")
    if n == 1:
        flash(f"Deleted the only SRAM file.")
    else:
        flash(f"All {n} SRAM files deleted.")
    return redirect(url_for('srams'))

# DEBUG
@app.route_delete('/tracks', auth, name="all versions of all tracks")
def tracks_delete():
    keys = list(store.items('track').keys())
    n = len(keys)
    if n:
        store.delete('track', keys)

    if not n:
        flash("No versions or tracks to delete!")
    elif n == 1:
        flash(f"Deleted the only track.")
    else:
        flash(f"Deleted {n} track versions.")

    return redirect(url_for('tracks'))

# DEBUG
@app.route('/long')
def long():
    return render_template('long.html', auth=auth)
