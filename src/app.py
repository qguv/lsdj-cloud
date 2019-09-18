#!/usr/bin/env python3

from . import auth
from . import store
from . import liblsdj
from . import models
from .flask import Flask

from flask import request, redirect, url_for, render_template, flash

from pathlib import Path
from werkzeug import exceptions
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
)

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
    return render_template('root.html')

@app.route('/login', methods=('GET', 'POST'))
@auth.login_form('root')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    auth.deauth()
    return redirect(url_for('root'))

@app.route('/srams', methods=('POST',))
@auth.required
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
                for name in trackpaths.keys():
                    store.assert_unused('track', name)

                # save them all in S3
                for name, path in trackpaths.items():
                    store.put('track', path, name=name)


            # success! store sram in s3
            sram_name = store.put('sram', f.name)
            flash(f"{len(trackpaths)} tracks saved from SRAM file {sram_name}.")

        # TODO automatically make a playlist for each uploaded SRAM
        # TODO you should optionally be able to fix an old version of a track on a playlist
        return redirect(url_for('srams'))

@app.route('/srams')
@auth.required
def srams():
    return render_template('srams.html', srams=sorted(models.srams().items()), total_size=store.usage('sram'))

@app.route('/tracks')
@auth.required
def tracks():
    tracks = sorted(models.tracks().items())
    total_size = store.usage('track')
    return render_template('tracks.html', tracks=tracks, total_size=total_size)

@app.route('/tracks/<name>')
@auth.required
def track(name):
    # TODO wasteful
    track = models.tracks()[name]
    return render_template('track.html', name=name, track=track)

@app.route('/srams/<name>/download')
@auth.required
def sram_download(name):
    return redirect(store.get_link('sram', name))

@app.route('/tracks/<name>/<int:version>/download')
@auth.required
def track_download(name, version):
    name = models.tracks()[name]['versions'][version]['full_name']
    return redirect(store.get_link('track', name))

@app.route_delete('/srams/<name>', name="this SRAM file")
@auth.required
def sram_delete(name):
    store.delete('sram', name)
    return redirect(url_for('srams'))

@app.route_delete('/tracks/<name>', name="all versions of this track")
@auth.required
def track_delete(name):
    tracks = models.tracks()

    res = redirect(url_for('tracks') if len(tracks) > 1 else url_for('srams'))

    track = tracks[name]
    store.delete('track', [version['full_name'] for version in track['versions'].values()])

    return res

@app.route_delete('/tracks/<name>/<int:version>', name="this version of the track")
@auth.required
def track_version_delete(name, version):
    tracks = models.tracks()
    track = tracks[name]
    version = track['versions'][version]

    res = redirect(url_for('track', name=name) if len(track['versions']) > 1 else url_for('tracks') if len(tracks) > 1 else url_for('srams'))

    store.delete('track', version['full_name'])
    return res

# DEBUG
@app.route_delete('/srams', name="all SRAM files")
@auth.required
def srams_delete():
    store.delete('sram', list(store.items('sram').keys()))
    return redirect(url_for('srams'))

# DEBUG
@app.route_delete('/tracks', name="all versions of all tracks")
@auth.required
def tracks_delete():
    store.delete('track', list(store.items('track').keys()))
    return redirect(url_for('tracks'))

# DEBUG
@app.route('/long')
def long():
    return render_template('long.html')
