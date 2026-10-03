"""Render every battle SFX ID in isolation (music stopped) to 32 kHz stereo WAV."""
import sys, json, struct, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from spcharness import *
from sfxparse import parse
STATE = sys.argv[1] if len(sys.argv) > 1 else paths.STATE
OUT = {'dry': os.path.join(paths.SFX, 'all'), 'wet': os.path.join(paths.SFX, 'all_wet')}
MAXS = 12.0
def render(s, sid, dry, cmd=0x08):
    s.reload()
    if dry: s.dry(True)
    s.play(0.25)
    s.command(0x0F)          # driver: key off everything, stop the music
    s.play(0.3)
    LIB.spc_clear_echo(s.p)  # drop the music's echo tail (twice: the echo pipeline refills once)
    s.play(0.1)
    LIB.spc_clear_echo(s.p)
    s.play(0.1)
    s.take()
    ok = s.sfx(sid, cmd=cmd)
    blk = 320; quiet = 0; started = False; t = 0
    while t < MAXS * SR:
        a = s.play(samples=blk); t += blk
        loud = np.abs(a.astype(int)).max() > 2
        if loud: started = True; quiet = 0
        else: quiet += blk
        if started and quiet > 0.6 * SR: break
        if not started and t > 1.5 * SR: break
    a = s.take()
    return ok, a, t >= MAXS * SR
def trim(a):
    # start: first sample above 1 LSB, walked back to the first non-zero sample (at most 1 ms: the wet path has a 1-LSB floor)
    m = np.abs(a.astype(int)).max(axis=1)
    nz2 = np.nonzero(m > 1)[0]
    if len(nz2) == 0: return a[:0]
    i0 = nz2[0]
    k = 0
    while i0 > 0 and m[i0 - 1] > 0 and k < 32: i0 -= 1; k += 1
    return a[i0:min(len(a), nz2[-1] + int(0.01 * SR))]
def event_state(data):
    rom = open(paths.ROM_PATH, 'rb').read()
    d = bytearray(data)
    d[0x100 + 0x3000:0x100 + 0x4600] = rom[0x042826:0x043E26]   # field/event SFX set in place of the battle set
    return bytes(d)
if __name__ == '__main__':
    KIND = os.environ.get('KIND', 'battle')
    data = open(STATE, 'rb').read()
    if KIND == 'event':
        data = event_state(data)
        OUT = {'dry': os.path.join(paths.SFX, 'event'), 'wet': os.path.join(paths.SFX, 'event_wet')}
        for v in OUT.values(): os.makedirs(v, exist_ok=True)
    for v in OUT.values(): os.makedirs(v, exist_ok=True)
    s = Spc(data)
    meta = {}
    for sid in range(256):
        ch = parse(KIND, sid)
        if not any(ch): continue
        for mode in ('dry', 'wet'):
            ok, a, capped = render(s, sid, mode == 'dry')
            b = trim(a)
            if len(b) == 0:
                meta.setdefault(sid, {})[mode] = {'ack': ok, 'silent': True}
                continue
            write_wav('%s/%03d.wav' % (OUT[mode], sid), b)
            pk = np.abs(b.astype(int)).max()
            meta.setdefault(sid, {})[mode] = {'ack': ok, 'dur': round(len(b) / SR, 3), 'peak_dbfs': round(20 * np.log10(pk / 32768), 1),
                                            'capped': capped}
        print(sid, meta[sid].get('dry'), flush=True)
    json.dump(meta, open(os.path.join(paths.WORK, 'sweep_meta_%s.json' % KIND), 'w'), indent=1)
