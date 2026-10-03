"""Where the capture reads and writes (all outside the repo: the ROM and everything rendered from it stay local).
  SMRPG_ROM      your Super Mario RPG (USA) dump, SHA-1 a4f7539054c359fe3f360b0e6b72e394439fe9df (default ~/games/smrpg/smrpg_usa.sfc)
  SMRPG_WORK     the audio-RAM dumps and logs (default ~/games/smrpg/work)
  SMRPG_SFX      the renders (default ~/games/smrpg/sfx): all/, all_wet/, event/, geno/ ...
  SPCRENDER_LIB  the renderer spcrender/build.sh builds (default $SMRPG_WORK/spcrender/libspc.dylib or .so)"""
import os, sys
ROM_PATH = os.path.expanduser(os.environ.get('SMRPG_ROM', '~/games/smrpg/smrpg_usa.sfc'))
WORK = os.path.expanduser(os.environ.get('SMRPG_WORK', '~/games/smrpg/work'))
SFX = os.path.expanduser(os.environ.get('SMRPG_SFX', '~/games/smrpg/sfx'))
SPCLIB = os.path.expanduser(os.environ.get('SPCRENDER_LIB', os.path.join(
    WORK, 'spcrender', 'libspc.dylib' if sys.platform == 'darwin' else 'libspc.so')))
STATE = os.path.join(WORK, 'spc', 'f4100.spc')     # the attract-demo battle's audio state (mesen.sh, then spcharness.py)
