"""The Forest Maze's art pass 2 (t7, richer): forest_tex.py paints the textures, blender/forest_scene.py builds the model
and bakes its light into vertex colours; this reads the result as stage-build faces and materials for stage_spec.py
(STAGE_ART=forest2, the default; STAGE_ART=forest is M3's art, greybox the greybox).
  CAP_STYLE=float|stem      the mushroom cap floating (t7) or on a thick stem behind the fighters' plane
  FOREST_BACK=0             the play plane alone (the edge lab's clean silhouette)
  STAR_ROAD=0               no shooting star (on by default: Michael, 2026-09-30)
  SKY_TIME_SCALE=N          every animation clock N times faster (the full-cycle readability measure only)
Outputs go to $MELEE_WORK/stage: art2/ (textures), forest_mesh.json, forest.blend.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import forest_tex

BLENDER = os.environ.get('BLENDER', '/opt/homebrew/bin/blender')
FOG = dict(start=60.0, end=560.0, color=[54, 46, 80])


def build(work):
    cap = os.environ.get('CAP_STYLE', 'float')
    play_only = os.environ.get('FOREST_BACK', '1') == '0'
    mats, tex_bytes = forest_tex.write(os.path.join(work, 'art2'))
    for k, m in mats.items():
        m['vertex'] = True                                   # the vanilla stages' mode: baked vertex colour x texture
        if k in ('branch', 'canopy'):
            m['alpha'] = 'cut'
        if k in ('mist', 'cloud_far', 'cloud_mid', 'cloud_near', 'treeline', 'treeline_far'):
            m['alpha'] = 'blend'                               # the treeline's soft edge: less busy behind the fighters
        if k.startswith('stars_') or k in ('streak', 'glowdot'):
            m['alpha'] = 'add'                                 # light added to the sky
        if k.startswith('stars_'):
            m['alpha_mat'] = True                              # the twinkle: an animated material alpha
    mesh = os.path.join(work, 'forest_mesh.json')
    cmd = [BLENDER, '-b', '--factory-startup', '--python', os.path.join(HERE, 'blender', 'forest_scene.py'), '--',
           '--out', mesh, '--blend', os.path.join(work, 'forest.blend'), '--cap', cap] + (['--play-only'] if play_only else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith('FOREST_SCENE')]
    if r.returncode or not line:
        sys.exit('forest_scene.py failed:\n' + (r.stdout + r.stderr)[-3000:])
    print(line[0].split(' triangles')[0][:200], 'triangles', line[0].rsplit(' ', 1)[1], f'texture bytes {tex_bytes}', file=sys.stderr)
    d = json.load(open(mesh))
    g = d['groups']
    return g.get('stage', []), g.get('back', []), mats, g.get('holo', []), d.get('joints', {}), d.get('anims', {})
