from flask import request, redirect, url_for, flash, session, escape, g
from urllib.parse import urlparse, parse_qs

from functools import wraps

def deauth():
    session.clear()
    flash("Logged out.")

def login_form(*, success_redirect: str):
    def decorator(wrapped):
        @wraps(wrapped)
        def wrapping(*args, **kwargs):

            if request.method == 'POST':

                # FIXME actually generate token
                session['t'] = request.form.get('password')

                if g.is_authenticated() and request.form.get('username'):
                    session['u'] = request.form['username']
                    flash(f"Welcome, {escape(session['u'])}.")

                    try:
                        return_to = parse_qs(urlparse(request.referrer).query)['r'][0]
                        return redirect(f"/{return_to}" if return_to else url_for(success_redirect))
                    except KeyError:
                        return redirect(url_for(success_redirect))

                flash('Invalid credentials!')
                # TODO query string will be lost on invalid credentials

            if request.args.get('r'):
                flash("You need to log in first.")

            return wrapped(*args, **kwargs)
        return wrapping
    return decorator

def required(wrapped):
    @wraps(wrapped)
    def wrapping(*args, **kwargs):
        if not g.is_authenticated():
            return redirect(url_for('login', r=request.full_path.lstrip('/').rstrip('?')))
        return wrapped(*args, **kwargs)
    return wrapping
