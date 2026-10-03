"""Where the arrangement's renderer finds its instruments and writes its renders: GENO_MUSIC (default
~/games/melee/work/music), outside the repo. It holds, as ../README.md lists them:
  libs/VSCO-2-CE-1.1.0, libs/emilyguitar, libs/growlybass (SFZ, CC0), libs/surge (Surge XT.vst3), libs/surge_data
  (its factory patches), tools/sfizz-1.2.3-macos (sfizz_render), sf/GeneralUser-GS-main (the choir), drums/aasimonster2
  (CC BY 4.0), amps/*.nam (NAM captures), and the renders (takes/, stems_draft2/, the draft WAVs)."""
import os
MUSIC = os.path.expanduser(os.environ.get('GENO_MUSIC', '~/games/melee/work/music'))
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')      # in the repo: the EQ target curve, the cue sheets
