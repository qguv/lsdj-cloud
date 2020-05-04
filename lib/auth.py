from flask import request, redirect, url_for, flash, session, escape, g
from lib.db import db
from urllib.parse import urlparse, parse_qs
from uuid import uuid4, UUID
from datetime import datetime
from models.user import User
from models.invitation import Invitation

from functools import wraps


class AuthError(Exception):
    pass


class Auth:
    def __init__(self, db, redis, bcrypt, token_ttl):
        self.db = db
        self.redis = redis
        self.bcrypt = bcrypt
        self.token_ttl = token_ttl

    def is_authenticated(self):
        try:
            uid = session['u']
            token = session['t']
        except KeyError:
            return False

        try:
            uid = UUID(uid)
        except ValueError:
            del session['u']
            return False

        try:
            if token != self.redis[f'token:{uid}']:
                return False
        except KeyError:
            return False

        g.user = User.query.get(uid)
        if g.user is None:
            del session['t']
            return False

        return True

    def deauth(self):
        if not self.is_authenticated():
            return

        uid = session['u']

        self.redis.delete(f'token:{uid}')
        del session['t']
        flash("Logged out.")

    def generate_token(self, uid):
        token = str(uuid4())
        self.redis.setex(f'token:{uid}', self.token_ttl, token)
        return token

    def signup_form(self, *, success_redirect: str):
        def decorator(wrapped):
            @wraps(wrapped)
            def wrapping(*args, **kwargs):

                if request.method == 'POST':
                    try:
                        # TODO atomic
                        try:
                            handle = request.form['h']
                            password = request.form['p']
                            invitation_id = request.form['i']
                        except KeyError:
                            raise AuthError()

                        if not invitation_id:
                            raise AuthError()

                        if len(handle) < 3:
                            raise AuthError(
                                "Handle must be at least 3 characters!"
                            )

                        if len(password) < 8:
                            return AuthError(
                                "Password must be at least 8 "
                                "characters!"
                            )

                        if password.lower() in ['password', handle.lower()]:
                            return AuthError(
                                "C'mon, pick a better password"
                            )

                        invitation = Invitation.query.get(invitation_id)
                        if invitation is None:
                            raise AuthError("Invitation is not valid")

                        if invitation.consumer:
                            raise AuthError("Invitation has been used already")

                        now = datetime.utcnow()
                        if invitation.expires <= now:
                            db.session.delete(invitation)
                            raise AuthError("Invitation has expired")

                        phash = self.bcrypt.generate_password_hash(password)
                        user = User(handle, phash)
                        user.last_login_on = now

                        invitation.used = now

                        db.session.add(invitation)
                        db.session.add(user)
                        db.session.commit()

                        token = self.generate_token(user.id)

                        # store session info
                        session['h'] = handle
                        session['u'] = user.id
                        session['t'] = token

                        flash(f"Welcome aboard, {escape(handle)}!")
                        return redirect(url_for(success_redirect))

                    except AuthError as e:
                        s = str(e) or (
                            "Please enter a referral code, handle, and "
                            "password."
                        )
                        flash(s)
                        # TODO auto-fill referral from last time

                # TODO auto-fill handle if known
                return wrapped(*args, **kwargs)
            return wrapping
        return decorator

    def login_form(self, *, success_redirect: str):
        def decorator(wrapped):
            @wraps(wrapped)
            def wrapping(*args, **kwargs):

                if request.method == 'POST':
                    try:

                        # TODO atomic
                        try:
                            handle = request.form['h']
                            password = request.form['p']
                        except KeyError:
                            raise AuthError()

                        user = User.query.filter_by(handle=handle).first()
                        if user is None:
                            raise AuthError()

                        if not self.bcrypt.check_password_hash(user.phash, password):  # noqa: E501
                            raise AuthError()

                        token = self.generate_token(user.id)

                        now = datetime.utcnow()
                        user.last_login_on = now
                        db.session.add(user)
                        db.session.commit()

                        # store session info
                        session['h'] = handle
                        session['u'] = user.id
                        session['t'] = token

                        flash(f"Welcome back, {escape(handle)}!")

                        try:
                            query = urlparse(request.referrer).query
                            return_to = parse_qs(query)['r'][0]
                            return redirect(
                                f"/{return_to}" if return_to
                                else url_for(success_redirect)
                            )
                        except KeyError:
                            return redirect(url_for(success_redirect))

                    # TODO query string will be lost
                    except AuthError as e:
                        s = str(e)
                        flash(s if s else "Login incorrect.")

                if request.args.get('r'):
                    # TODO different messages for timeout and unauthenticated
                    flash("You need to log in first.")

                # TODO auto-fill handle if known
                return wrapped(*args, **kwargs)
            return wrapping
        return decorator

    def required(self):
        def decorator(wrapped):
            @wraps(wrapped)
            def wrapping(*args, **kwargs):
                if self.is_authenticated():
                    return wrapped(*args, **kwargs)
                else:
                    url = request.full_path.lstrip('/').rstrip('?')
                    return redirect(url_for('login', r=url))
            return wrapping
        return decorator
