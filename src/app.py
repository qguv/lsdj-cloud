#!/usr/bin/env python3

from . import auth
from . import store

from flask import request, Response, redirect, url_for, render_template, flash, send_file
from flask import Flask as _Flask

from pathlib import Path

class Flask(_Flask):
    jinja_options = _Flask.jinja_options.copy()

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
    return auth.deauth(redirect(url_for('root')))

@app.route('/sram', methods=('GET', 'POST'))
@auth.required
def sram():
    if request.method == 'POST':
        try:
            name = store.put('sram', request.files['sram'])
            flash(f"New SRAM {name} saved.")
        except KeyError:
            flash("No file provided")

    mb = f"{store.usage('sram') / 1000:.1f}"
    return render_template('sram.html', files=store.iter('sram'), megabytes=mb)

@app.route('/sram/<filename>')
@auth.required
def get_sram(filename):
    return redirect(store.get_link('sram', filename))

@app.route('/sram/<filename>/delete')
@auth.required
def delete_sram(filename):
    store.delete('sram', filename)
    flash(f"Deleted {filename}.")
    return redirect(url_for('sram'))
