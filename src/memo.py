from flask import g

from functools import wraps

def memo(f):
    @wraps(f)
    def wrapping(*args, **kwargs):
        assert not kwargs, "functions accepting kwargs can't be memo'd yet!" # TODO

        if 'memo' not in g:
            g.memo = dict(stats=dict())

        f_memo = g.memo[f] = g.memo.get(f, dict())
        f_stats = g.memo['stats'][f] = g.memo['stats'].get(f, dict(hit=0, miss=0))

        try:
            v = f_memo[args]
            f_stats['hit'] += 1

        except KeyError:
            v = f(*args)
            f_memo[args] = v
            f_stats['miss'] += 1

        print(f"DEBUG\n{f.__name__}: {f_stats}\n")
        return v

    return wrapping

