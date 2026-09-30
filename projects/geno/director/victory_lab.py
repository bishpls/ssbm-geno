"""Victory lab: a two-stock match that ends as soon as it can (the loser dropped under the blast zone twice), then the
results screen, where the winner plays one of his win poses (GmRstMGe.dat, datkit DemoBuild.cs) and the loser claps.
The pose is the button the winner's pad holds as the screen opens (B Win1, Y Win2, X Win3; none: one at random): the
director's menu pads hold it on the master pad status from WIN_AT (a loop frame since boot; the SCENE lines of a first
run say when the results scene starts) to the end.
    WIN_BTN=B WIN_AT=900 .venv/bin/python tools/machinima/melee/build.py projects/geno victory_lab
    WIN_LOSER=geno ... : Geno loses instead (his Lose clap), Fox wins
    WIN_PAIR=mario,fox ... : any two fighters (first wins unless WIN_LOSER=geno/first): a vanilla baseline
The music comes back on when the results scene opens (dir_results_music), so the winner's victory fanfare plays (Geno's:
ff_geno.hps; WIN_MUSIC=0 keeps the director's silence). The results scene opens at loop frame 461 with the defaults, so a
pose button wants WIN_AT at or before that (e.g. WIN_AT=440).
"""
import os, sys
from dsl import Film, BTN

loser_is_geno = os.environ.get('WIN_LOSER') in ('geno', 'first')      # the first player of the pair loses
a, b = os.environ.get('WIN_PAIR', 'geno,fox').split(',')
f = Film(len_s=16.0)
f.setup(players=[(a, dict(x=-30, face=1)), (b, dict(x=30, face=-1))], seed=int(os.environ.get('WIN_SEED', 5)), stocks=2)
f.cam(0, eye=(0, 30, 260), at=(0, 15, 0), fov=35, ease='cut')
lose = 0 if loser_is_geno else 1
f.port(lose).hold(60, 3, btn='X')                    # airborne, so the teleport takes
f.setpos(68, lose, 0, -260)
f.port(lose).hold(330, 3, btn='X')
f.setpos(338, lose, 0, -260)
path = f.emit(sys.argv[1])
if os.environ.get('WIN_MUSIC', '1') != '0':
    s = open(path).read()
    assert 'const int dir_results_music = 0;' in s
    open(path, 'w').write(s.replace('const int dir_results_music = 0;', 'const int dir_results_music = 1;'))

btn, at = os.environ.get('WIN_BTN', ''), int(os.environ.get('WIN_AT', 0))
if btn:
    win = 1 if loser_is_geno else 0
    s = open(path).read()
    s = s.replace('const int dir_nmenu_pads = 0;', 'const int dir_nmenu_pads = 1;')
    s = s.replace('const DirMenuPad dir_menu_pads[] = { { 0 } };',
                  f'const DirMenuPad dir_menu_pads[] = {{ {{ {at}, {win}, 0, 0x{BTN[btn]:X}, 0, 0, 0, 0 }} }};')
    open(path, 'w').write(s)
