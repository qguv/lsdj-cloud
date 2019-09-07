from flask import request, redirect, url_for, flash, current_app

from functools import wraps

'''Checks to see if a request is authenticated with a valid token.'''
def is_authenticated() -> bool:
    # FIXME actually check token here
    return bool(request.cookies.get('t'))

def deauth(response):
    response.set_cookie('t', '', expires=0)
    flash("Logged out.")
    return response

'''Decorate your login form rendering route with this.'''
def login_form(success_redirect_route: str):
    def decorator(wrapped):
        @wraps(wrapped)
        def wrapping(*args, **kwargs):
            if request.method == 'POST':

                # FIXME actually check credentials
                if request.form.get('username') and request.form.get('password'):
                    response = redirect(url_for(success_redirect_route))
                    response.set_cookie('t', 'ok', max_age=3600, secure=not current_app.debug)
                    flash("Logged in.")
                    return response
                else:
                    flash('Invalid credentials!')

            return wrapped(*args, **kwargs)
        return wrapping
    return decorator

'''Decorator'''
def required(wrapped):
    @wraps(wrapped)
    def wrapping(*args, **kwargs):
        if not is_authenticated():
            flash("You need to log in first.")
            return redirect(url_for('login'))
        return wrapped(*args, **kwargs)
    return wrapping
