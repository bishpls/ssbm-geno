"""Read-only planner: byte budget and the exact .ssm fields to rewrite so that sfx 510017 (entry 17) plays a new take.
Reads the disc's nr_name.ssm files (never writes them). Field values are computed; the DSP coefficients and the
initial predictor/scale come from the DSP-ADPCM encoder's header for the actual encode."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import soundfile as sf
import ssm

DISC = os.path.join(os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc')), 'files', 'audio')
BUDGET = 348160                     # DOL table offsets_arr_803BC4E4[51][0]: ARAM bytes the game books for nr_name

def nibbles(n):                     # DSP-ADPCM nibble count for n samples (frame = 1 header byte + 14 sample nibbles)
    return (n // 14) * 16 + ((n % 14) + 2 if n % 14 else 0)

def frame_bytes(n):
    return -(-n // 14) * 8

def fields(B, n):
    s = 2 * B + 2
    return dict(start_nibble=s, loop_start_nibble=s, end_nibble=2 * B + nibbles(n) - 1)

def slot_region(bank, i):
    c = bank['sounds'][i]['chans'][0]
    B = (c['cur'] - 2) // 2
    return B, (c['end'] // 16 + 1) * 8 - B

def plan(wavs):
    us = ssm.parse(os.path.join(DISC, 'us', 'nr_name.ssm')); jp = ssm.parse(os.path.join(DISC, 'nr_name.ssm'))
    tail_us = (us['sounds'][-1]['chans'][0]['end'] // 16 + 1) * 8
    B_app = -(-us['dlen'] // 32) * 32          # append after the existing 16-byte pad, 32-byte aligned
    room = BUDGET - B_app
    print(f"US nr_name.ssm: data_off=0x{us['data_off']:X} data_len={us['dlen']} (samples end at {tail_us}); "
          f"append at data byte {B_app}; room to the {BUDGET}-byte budget: {room} B = {room // 8} frames = "
          f"{room // 8 * 14} samples = {room // 8 * 14 / 12000:.3f} s")
    for tag, bank in (('US', us), ('JP', jp)):
        for i in (9, 17):
            B, nb = slot_region(bank, i)
            print(f"{tag} slot {i:2d}: data byte {B}, {nb} B -> max {nb // 8 * 14} samples = {nb // 8 * 14 / 12000:.3f} s")
    print()
    B9u, n9u = slot_region(us, 9); B9j, n9j = slot_region(jp, 9); B17u, n17u = slot_region(us, 17)
    rows = []
    for w in wavs:
        x, sr = sf.read(w); n = len(x); fb = frame_bytes(n); add = -(-fb // 32) * 32
        r = dict(file=os.path.basename(w), dur=n / sr, samples=n, adpcm_bytes=fb)
        r['us_slot17_inplace'] = fb <= n17u
        r['us_slot9_inplace'] = fb <= n9u
        r['jp_slot9_inplace'] = fb <= n9j
        r['us_append'] = dict(new_data_len=B_app + add, file_size=us['data_off'] + B_app + add,
                              headroom_left=BUDGET - B_app - add, **fields(B_app, n))
        r['us_slot9'] = fields(B9u, n) if r['us_slot9_inplace'] else None
        r['jp_slot9'] = fields(B9j, n) if r['jp_slot9_inplace'] else None
        rows.append(r)
        a = r['us_append']
        print(f"{r['file']:24s} {n / sr:.3f}s {n:6d} smp  ADPCM {fb:5d} B | slot17 {'fits' if r['us_slot17_inplace'] else 'no'}"
              f" | US slot9 {'fits' if r['us_slot9_inplace'] else 'no'} | JP slot9 {'fits' if r['jp_slot9_inplace'] else 'no'}")
        print(f"    US append: data_len {us['dlen']} -> {a['new_data_len']} (+{add}), file {us['data_off'] + us['dlen']} -> "
              f"{a['file_size']} B, headroom left {a['headroom_left']} B; entry17: start=loop_start={a['start_nibble']} "
              f"(0x{a['start_nibble']:X}), end={a['end_nibble']} (0x{a['end_nibble']:X})")
        if r['us_slot9']:
            f = r['us_slot9']; print(f"    US in slot 9's region (no growth): start=loop_start={f['start_nibble']} "
                                     f"(0x{f['start_nibble']:X}), end={f['end_nibble']} (0x{f['end_nibble']:X})")
        if r['jp_slot9']:
            f = r['jp_slot9']; print(f"    JP in slot 9's region (no growth): start=loop_start={f['start_nibble']} "
                                     f"(0x{f['start_nibble']:X}), end={f['end_nibble']} (0x{f['end_nibble']:X})")
    return rows

if __name__ == '__main__':
    plan(sys.argv[1:])
