"""Shield lab: Geno and an opponent (SHIELD_OPP, default fox) hold a full hard shield; the director logs each one's shield
sphere (ThrowN's world centre and scale) and every hurtbox capsule in world space (SHIELD/HURT lines), for the coverage
check in labs/shield_cover.py: at full shield no hurtbox may reach outside the bubble (no shield pokes).
    SHIELD_OPP=marth .venv/bin/python tools/machinima/melee/build.py projects/geno shield_lab
"""
import os, sys
from dsl import Film

OPP = os.environ.get('SHIELD_OPP', 'fox')
f = Film(len_s=4.0)
f.setup(players=[('geno', dict(x=-15, face=1)), (OPP, dict(x=15, face=-1))], seed=5, coll=1)
f.cam(0, eye=(0, 12, 110), at=(0, 9, 0), fov=30, ease='cut')
for port in (0, 1):
    f.port(port).hold(20, 190, btn='R')
for t in [int(x) for x in os.environ.get("SHIELD_AT", "70,140").split(",")]:
    f.shield(t, 0); f.shield(t + 1, 1)
f.emit(sys.argv[1])
