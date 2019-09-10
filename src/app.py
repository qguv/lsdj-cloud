#!/usr/bin/env python3

from . import auth
from . import store
from . import liblsdj
from . import misc

from flask import request, redirect, url_for, render_template, flash
from flask import Flask

from pathlib import Path
from werkzeug import exceptions
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='../static', template_folder='../templates')

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

@app.route('/srams')
@auth.required
def srams():
    mb = f"{store.usage('sram') / 1000:.1f}"
    return render_template('srams.html', srams=store.items('sram'), mb=mb)

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
                trackpaths = {secure_filename(p.stem): str(p) for p in Path(d).iterdir()}

                # ensure all paths are free
                for name in trackpaths.keys():
                    store.assert_unused('track', name)

                # save them all in S3
                for name, path in trackpaths.items():
                    store.put('track', path, name=name)


            # success! store sram in s3
            sram_name = store.put('sram', f.name)
            flash(f"{len(trackpaths)} tracks saved from SRAM {sram_name}.")

        # TODO automatically make a playlist for each uploaded SRAM
        # TODO you should optionally be able to fix an old version of a track on a playlist
        return redirect(url_for('srams'))

@app.route('/tracks')
@auth.required
def tracks():
    tracks = sorted(store.items('track').items())
    mb = f"{store.usage('track') / 1000:.1f}"
    return render_template('tracks.html', tracks=tracks, mb=mb)

@app.route('/tracks/<name>')
@auth.required
def track(name):
    store.assert_exists('track', name)
    obj = store.items('track')[name]
    mb = f"{obj.size / 1000:.1f}"
    return render_template('track.html', name=name, mb=mb)

@app.route('/srams/<name>/download')
@auth.required
def sram_download(name):
    return redirect(store.get_link('sram', name))

@app.route('/tracks/<name>/download')
@auth.required
def track_download(name):
    return redirect(store.get_link('track', name))

# DEBUG
@app.route('/srams/<name>/delete', methods=('GET', 'POST'))
@auth.required
@misc.confirm_delete("SRAM")
def sram_delete(name):
    store.delete('sram', name)
    return redirect(url_for('srams'))

# DEBUG
@app.route('/tracks/<name>/delete', methods=('GET', 'POST'))
@auth.required
@misc.confirm_delete("track")
def track_delete(name):
    store.delete('track', name)
    return redirect(url_for('tracks'))

# DEBUG
@app.route('/srams/delete', methods=('GET', 'POST'))
@auth.required
@misc.confirm_delete("all SRAMs")
def srams_delete():
    for name in store.items('sram'):
        store.delete('sram', name)
    return redirect(url_for('srams'))

# DEBUG
@app.route('/tracks/delete', methods=('GET', 'POST'))
@auth.required
@misc.confirm_delete("all tracks")
def tracks_delete():
    for name in store.items('track'):
        store.delete('track', name)
    return redirect(url_for('tracks'))

# DEBUG
@app.route('/long')
def long():
    return render_template('long.html')
