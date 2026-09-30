"""Data > VS Records from the main menu, to see Geno's face and name in the records list (frames every 20).
    .venv/bin/python tools/machinima/melee/build.py projects/geno records_lab
"""
import sys
from dsl import Menu

m = Menu(boot='menu', len_s=28.0)
t = 120
for k in range(4):                                     # main menu: down to Data (menus read the D-pad)
    m.press(t, 0, 'DD'); t += 20
m.press(t, 0, 'A'); t += 60
for k in range(2):                                     # Data: down to VS Records
    m.press(t, 0, 'DD'); t += 20
m.press(t, 0, 'A'); t += 60
m.press(t, 0, 'A'); t += 80                            # into the first records page
for k in range(26):                                    # to the last column (Geno) and the last row
    m.press(t, 0, 'DR'); t += 12
for k in range(26):
    m.press(t, 0, 'DD'); t += 12
m.emit(sys.argv[1])
