from flask import Flask as _Flask
from flask import request, render_template, flash

from functools import wraps, update_wrapper

class Flask(_Flask):
    def route_delete(self, rule, auth, name=None, **route_kwargs):
        '''
        Decorates a function that deletes an object. Renders a form that asks
        the user first.
        '''
        delete_route_kwargs = route_kwargs.copy()
        delete_route_kwargs['methods'] = ('DELETE',)

        route_kwargs['methods'] = ('GET', 'POST')

        def wrapping(f):
            @auth.required()
            @wraps(f)
            def delete(*args, **kwargs):
                res = f(*args, **kwargs)
                return res

            @self.route(f"{rule.rstrip('/')}/delete", **route_kwargs)
            @auth.required()
            @wraps(f)
            def get_post(*args, **kwargs):
                if request.method == "GET":
                    return render_template("delete.html", name="this" if name is None else name, auth=auth)
                return delete(*args, **kwargs)

            self.add_url_rule(rule, f.__name__ + '_DELETE', delete, **delete_route_kwargs)

            return get_post
        return wrapping
