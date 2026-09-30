"""walk_lab's camera keys (script frame, ease, x offset of the tracked view), read from the lab itself, for walk_board."""
import os, sys, tempfile


def keys():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, '..', '..', '..', '..', 'tools', 'machinima', 'melee'))
    import dsl
    grabbed = []
    real = dsl.Film.emit
    dsl.Film.emit = lambda self, path: grabbed.append(self)
    try:
        g = {'__name__': 'walk_lab', '__file__': os.path.join(here, '..', 'walk_lab.py')}
        argv, sys.argv = sys.argv, ['walk_lab', os.path.join(tempfile.mkdtemp(), 'walk_lab.c')]
        exec(compile(open(g['__file__']).read(), g['__file__'], 'exec'), g)
    except SystemExit:
        pass
    finally:
        sys.argv = argv
        dsl.Film.emit = real
    f = grabbed[0]
    return sorted((s, ease, at[0]) for s, ease, eye, at, fov, roll, tr in f.cams)
