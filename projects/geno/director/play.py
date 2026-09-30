"""A build for playing by hand: boot into VS mode with every character and stage unlocked, and no scripted input.
GENO_COLL=1 (or 2) turns on the developer display of hitboxes and hurtboxes (2: the capsules only).
    GENO_COLL=1 .venv/bin/python tools/machinima/melee/build.py projects/geno play
"""
import os, sys
from dsl import Menu

Menu(boot='vs', len_s=1.0, coll=int(os.environ.get('GENO_COLL', '0'))).emit(sys.argv[1])
