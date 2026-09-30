"""Edge lab: the Forest Maze's model edges against its collision, in pixels. Two eye-level shots on the free camera, one
at the main floor's height and one at the cap's, so each top surface is edge-on: its top edge must sit on the image's
centre row, and its ends at the collision's x (projected at the face's depth, from the spec: FRONT for the stump, 14 for
the cap). Fighters stand out of the way at x = +-45.
    .venv/bin/python tools/machinima/melee/build.py projects/geno/stage edge_lab
    DOLPHIN_SLOTS=2 .venv/bin/python tools/machinima/dolphin.py run $MELEE_DISC/sys/main.dol RUN --frames 130 --res 2 --quiet
    .venv/bin/python projects/geno/stage/director/edge_lab.py --report RUN [OUT.json]
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import layouts, stage_spec  # noqa: E402

DIST, FOV, ASPECT = 300.0, 30.0, 1.2173        # Melee projects at 1.2173 (HANDOFF §5)
CAP = layouts.CANDIDATES['clearing']['platforms'][0]
L = layouts.BODY['ledge_x']
SHOTS = [dict(name='floor', y=0.0, frame=50, ends=[(-L, stage_spec.FRONT), (L, stage_spec.FRONT)], span=(-60, 60)),
         dict(name='cap', y=CAP['y'], frame=110, ends=[(CAP['x0'], 14.0), (CAP['x1'], 14.0)], span=(-20, 20))]


def build(out_c):
    from dsl import Film
    f = Film(len_s=130 / 60.0)
    f.setup(players=[('fox', dict(x=-45, face=1)), ('falco', dict(x=45, face=-1))], stage='forest_maze', seed=1)
    for i, s in enumerate(SHOTS):
        t0 = 0 if i == 0 else 60
        f.cam(t0, eye=(0, s['y'], DIST), at=(0, s['y'], 0), fov=FOV, ease='cut')
    f.cue(125, 'end')
    f.emit(out_c)


def project(x, y, z, cy, W, H):
    t = math.tan(math.radians(FOV / 2))
    d = DIST - z
    return W / 2 + x / (d * t * ASPECT) * W / 2, H / 2 - (y - cy) / (d * t) * H / 2


def report(run, out=None):
    import numpy as np
    from PIL import Image
    res = []
    for s in SHOTS:
        im = np.asarray(Image.open(os.path.join(run, f"f{s['frame'] + 8:05d}.png")).convert('RGB')).astype(float)
        H, W = im.shape[:2]
        lum = im.mean(2)
        # the top edge: the strongest vertical step within 20 rows of the centre, at columns across the surface
        rows = []
        for x in np.linspace(s['span'][0], s['span'][1], 9):
            if abs(abs(x) - 45) < 10: continue                      # the fighters stand at +-45
            px = int(round(project(x, s['y'], 0, s['y'], W, H)[0]))
            col = lum[H // 2 - 20:H // 2 + 20, px - 1:px + 2].mean(1)
            g = np.abs(np.diff(col))
            rows.append(H // 2 - 20 + int(np.argmax(g)) + 1)          # the step between rows i and i+1 is the edge i+1
        # the ends: the strongest horizontal step 3-6 rows under the edge, near each projected end
        ends = []
        for x, z in s['ends']:
            ex, _ = project(x, s['y'], z, s['y'], W, H)
            band = lum[H // 2 + 3:H // 2 + 7, int(ex) - 25:int(ex) + 26].mean(0)
            g = np.abs(np.diff(band))
            found = int(ex) - 25 + int(np.argmax(g)) + 1
            ends.append(dict(x=x, z=z, expected_px=round(ex, 2), found_px=found, err_px=round(found - ex, 2)))
        expected_row = H / 2
        res.append(dict(shot=s['name'], surface_y=s['y'], expected_row=expected_row, rows=rows,
                        row_err_px=round(max(abs(r - expected_row) for r in rows), 2), ends=ends,
                        end_err_px=round(max(abs(e['err_px']) for e in ends), 2),
                        px_per_unit=round(H / 2 / (DIST * math.tan(math.radians(FOV / 2))), 3)))
    ok = all(r['row_err_px'] <= 1.0 and r['end_err_px'] <= 1.0 for r in res)
    rep = dict(ok=ok, shots=res)
    if out: json.dump(rep, open(out, 'w'), indent=1)
    print(json.dumps(rep, indent=1))
    return rep


if __name__ == '__main__':
    if sys.argv[1] == '--report':
        report(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        build(sys.argv[1])
