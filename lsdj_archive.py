from pathlib import Path
from time import time

from flask import Flask, request, redirect, url_for, render_template, Response

app = Flask('lsdj_archive')

@app.route('/')
def root():
    return redirect(url_for('sram')) # TODO do something real here

@app.route('/sram')
def sram():
    '''list sram files'''
    return render_template('sram.html', sram_filenames=[f.name for f in Path('./sram').glob('*.sram')])

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
        return Response("File not saved! " + str(e), status=401)

    #toast("New SRAM successfully saved.")
    return redirect(url_for('sram'))

app.run(debug=True)
