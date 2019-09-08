from flask import request, redirect, url_for, flash, session, escape

from functools import wraps

def deauth(response):
    session.clear()
    flash("Logged out.")
    return response

def login_form(success_redirect_route: str):
    def decorator(wrapped):
        @wraps(wrapped)
        def wrapping(*args, **kwargs):
            if request.method == 'POST':

                # FIXME actually check credentials
                if request.form.get('username') and request.form.get('password'):
                    session['u'] = request.form['username']
                    session['t'] = "fake token" # FIXME generate this
                    flash(f"Welcome, {escape(session['u'])}.")
                    return redirect(url_for(success_redirect_route))
                else:
                    flash('Invalid credentials!')

            return wrapped(*args, **kwargs)
        return wrapping
    return decorator

def required(wrapped):
    @wraps(wrapped)
    def wrapping(*args, **kwargs):
        if 't' not in session:
            flash("You need to log in first.")
            return redirect(url_for('login'))
        return wrapped(*args, **kwargs)
    return wrapping
