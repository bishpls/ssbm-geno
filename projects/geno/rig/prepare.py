"""Read the inputs Geno's fighter build takes from your own disc into $MELEE_WORK, once, before rig.py / anims.py /
fighter-build (HANDOFF §4) and the menu art:
    .venv/bin/python projects/geno/rig/prepare.py            # needs datkit (.NET 8) and the extracted disc at $MELEE_DISC
  $MELEE_WORK/rig/mr_actions.txt      Mario's action table (`datkit actions`): anims.py builds Geno's table on it, action
                                      for action (the template's names, flags and frame counts)
  $MELEE_WORK/rig/mr_aj/NNN.dat       Mario's animations, one file per action (the same command)
  $MELEE_WORK/rig/mr_rootmotion.json  TransN's path per frame (`datkit rootmotion`) for every common action that moves by its
                                      animation (flag bit 31: rolls, get-ups, ledge actions, dash attack, the throws'
                                      victims); anims.py borrows these paths where Geno's own keys leave TransN still.
                                      Without this file those actions leave him standing still
  $MELEE_WORK/css3/j*_*.png           the character select's own icon frames and name-band letters (`datkit texdump` of
                                      the vanilla MnSlChr.usd), which css/placeholder.py and menus/portrait.py cut from
Everything written is derived from the disc: it stays in the work folder, never in git. Run it before installing Geno's
menus (it needs the vanilla MnSlChr.usd; once Geno's is installed, point MNSLCHR at a vanilla copy).
"""
import json, os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
DATKIT = os.path.join(ROOT, 'tools', 'machinima', 'melee', 'datkit.sh')
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
WORK = os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work'))
ROOT_MOTION = 0x80000000
FIRST_SPECIAL = 0x127          # the template's special-move actions start here; Geno's specials are his own, so no paths
RX = re.compile(r'^\s*(\d+) 0x\w+ off\s+(\d+) size\s+(\d+) flags (\w+) script')


def dk(*args):
    r = subprocess.run([DATKIT, *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'datkit {args[0]} failed:\n{r.stdout[-2000:]}{r.stderr[-2000:]}')
    return r.stdout


def main():
    files = os.path.join(DISC, 'files')
    rig = os.path.join(WORK, 'rig'); aj = os.path.join(rig, 'mr_aj')
    os.makedirs(aj, exist_ok=True)
    table = dk('actions', os.path.join(files, 'PlMr.dat'), os.path.join(files, 'PlMrAJ.dat'), aj)
    open(os.path.join(rig, 'mr_actions.txt'), 'w').write(table)
    paths = {}
    for line in table.splitlines():
        m = RX.match(line)
        if not m:
            continue
        idx, size, flags = int(m.group(1)), int(m.group(3)), int(m.group(4), 16)
        if flags & ROOT_MOTION and size > 0 and idx < FIRST_SPECIAL:
            paths[str(idx)] = json.loads(dk('rootmotion', os.path.join(aj, f'{idx:03d}.dat')))
    json.dump(paths, open(os.path.join(rig, 'mr_rootmotion.json'), 'w'))
    mn = os.path.expanduser(os.environ.get('MNSLCHR', os.path.join(files, 'MnSlChr.usd')))
    dk('texdump', mn, 'MnSelectChrDataTable', 'MenuModel', os.path.join(WORK, 'css3'), '16,17,23,24')
    print(f'{rig}/mr_actions.txt, mr_aj/ ({len(os.listdir(aj))} animations), mr_rootmotion.json ({len(paths)} paths); '
          f'{WORK}/css3/ (icon frames)')


if __name__ == '__main__':
    main()
