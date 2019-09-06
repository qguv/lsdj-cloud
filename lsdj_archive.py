from pathlib import Path
from time import time

from flask import Flask, Response, request, redirect, url_for, render_template, make_response, flash

app = Flask('lsdj_archive')

# TODO make this a decorator return redirect
# TODO set query parameter on redirect to return to this URL after logging in
def is_authenticated() -> Response or None:
    token = request.cookies.get('token')
    # FIXME actually check token
    return bool(token)

@app.route('/')
def root():
    if not is_authenticated():
        return redirect(url_for('login'))

    # TODO real homepage, not just redirect
    return redirect(url_for('sram'))

@app.route('/login', methods=('GET', 'POST'))
def login():

    if response.method == "GET":
        return render_template('login.html')

    res = make_response(redirect(url_for('root')))

    # FIXME actually check credentials
    token = 'ok'
    res.set_cookie('token', token)
    flash("Logged in (fake)!")
    return res

# FIXME check auth? or group by user?
@app.route('/sram')
def sram():
    '''list sram files'''
    return render_template('sram.html', sram_filenames=[f.name for f in Path('./sram').glob('*.sram')])

# FIXME check auth
@app.route('/sram/new', methods=('POST',))
def new_sram():
    '''form target to upload an LSDj SRAM file'''

    filename = str(time())
    filename = filename.replace('.', '_')
    filename = filename + '.sram'

    try:
        f = request.files['sram']
        f.save('sram/' + filename)
    except Exception as e:
        # TODO flash+redirect here? maybe in the sram upload form template?
        return Response("File not saved! " + str(e), status=401)

    flash("New SRAM successfully saved.")
    return redirect(url_for('sram'))

app.run(debug=True)
