from flask import request, render_template, flash

from functools import wraps

def confirm_delete(resource_name):
    def wrapping(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if request.method == "GET":
                return render_template("delete.html", resource=resource_name)
            res = f(*args, **kwargs)
            flash(f"Deleted {resource_name}.")
            return res
        return wrapped
    return wrapping
