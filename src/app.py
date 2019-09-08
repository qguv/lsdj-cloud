#!/usr/bin/env python3

from . import auth
from . import store

from flask import Flask, request, redirect, url_for, render_template, flash, send_file

from pathlib import Path

app = Flask(__name__, static_folder='../static', template_folder='../templates')

@app.route('/')
def root():
    return render_template('root.html', auth=auth)

@app.route('/login', methods=('GET', 'POST'))
@auth.login_form('root')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    return auth.deauth(redirect(url_for('root')))

@app.route('/sram', methods=('GET', 'POST'))
@auth.required
def sram():
    if request.method == 'POST':
        try:
            name = store.put(request.files['sram'])
            flash(f"New SRAM {name} saved.")
        except KeyError:
            flash("No file provided")

    return render_template('sram.html', sram_filenames=[f.name for f in Path('./sram').glob('*.sram')])

@app.route('/sram/<filename>')
@auth.required
def get_sram(filename):
    # FIXME sanitize
    with store.get(filename) as f:
        # FIXME does this work
        return send_file(f, mimetype="application/octet-stream")
