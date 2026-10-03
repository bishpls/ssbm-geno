"""Verification of the DSP-ADPCM encoder/decoder chain.
 A. Port vs reference: the Python port and the reference C (jackoalan grok.c, compiled from source into the
    scratchpad) must produce byte-identical coefficients and frames for the same PCM.
 B. Geno clip: encode -> decode -> SNR vs the source WAV.
 C. Game data: an existing nr_name clip decoded from the disc bank with tools/ssm.py; (1) re-encoding it with the
    game's own stored coefficients must reproduce the stored frames (checks our decoder against the stored data:
    the stored frames are the exact ADPCM of our decode); (2) full round trip with fresh coefficients -> SNR."""
import sys, os, subprocess, tempfile, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf
import dspenc, ssm

HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
REFENC = os.environ.get('REFENC')          # path to the compiled reference harness (optional)
BANK = os.path.join(os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc')), 'files', 'audio', 'us', 'nr_name.ssm')

def ref_encode(pcm):
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, 'in.raw'), os.path.join(d, 'out.bin')
        np.asarray(pcm, '<i2').tofile(a)
        subprocess.run([REFENC, a, b], check=True)
        raw = open(b, 'rb').read()
    coefs = np.frombuffer(raw[:32], '<i2').reshape(8, 2)
    return [tuple(int(v) for v in c) for c in coefs], raw[32:]

def stored_clip(bank, i):
    c = bank['sounds'][i]['chans'][0]
    data = bank['raw'][bank['data_off']:]
    B = (c['cur'] - 2) // 2; nb = (c['end'] // 16 + 1) * 8 - B
    coefs = [(c['coefs'][2 * k], c['coefs'][2 * k + 1]) for k in range(8)]
    return data[B:B + nb], coefs, ssm.decode_channel(bank, c), c

def main():
    res = {}
    geno, sr = sf.read(os.path.join(HERE, 'geno_CD_full.wav'), dtype='int16')
    bank = ssm.parse(BANK)
    # ---- A. port vs reference
    if REFENC:
        tests = {'geno_CD_full': geno}
        for i in (4, 21, 28):   # Falco, Mario, Pichu as decoded from the disc
            tests[f'nr_name[{i}] decoded'] = stored_clip(bank, i)[2]
        for name, pcm in tests.items():
            d_py, info = dspenc.encode(pcm); c_ref, d_ref = ref_encode(pcm)
            same_c = [tuple(c) for c in info['coefs']] == c_ref
            nsame = sum(d_py[k:k + 8] == d_ref[k:k + 8] for k in range(0, len(d_ref), 8))
            res[f'A {name}'] = dict(coefs_identical=same_c, frames_identical=f'{nsame}/{len(d_ref)//8}',
                                    bytes_identical=d_py == d_ref)
            print(f'A  port vs reference C on {name:22s}: coefs identical={same_c}  frames identical {nsame}/{len(d_ref)//8}'
                  f'  all bytes identical={d_py == d_ref}')
    # ---- B. Geno encode
    data, info = dspenc.encode(geno)
    y = dspenc.decode(data, info['coefs'], len(geno))
    err = geno.astype(int) - y.astype(int)
    res['B geno'] = dict(samples=len(geno), frames=info['frames'], bytes=len(data), ps=info['ps'],
                         coefs=info['coefs'], snr_db=round(dspenc.snr_db(geno, y), 2),
                         rms_err=round(float(np.sqrt(np.mean(err ** 2.0))), 1), max_abs_err=int(np.abs(err).max()))
    print(f"B  geno_CD_full: {len(geno)} samples @ {sr} Hz -> {info['frames']} frames = {len(data)} B; ps=0x{info['ps']:02X}; "
          f"SNR {res['B geno']['snr_db']} dB (rms err {res['B geno']['rms_err']}, max {res['B geno']['max_abs_err']})")
    # ---- C. game data
    for i in (4, 28, 21):
        stored, coefs, pcm, c = stored_clip(bank, i)
        # C1: frame encoder with the game's coefficients on our decode of the stored frames
        conv = [0] * 16; nsame = 0; nf = len(stored) // 8; maxdiff = 0; out = bytearray()
        for p in range(nf):
            chunk = [int(v) for v in pcm[p * 14:p * 14 + 14]]
            conv[2:16] = chunk + [0] * (14 - len(chunk))
            blk, conv = dspenc.encode_frame(conv, 14, coefs)
            out += blk; nsame += blk == stored[p * 8:p * 8 + 8]
            conv[0] = conv[14]; conv[1] = conv[15]
        y1 = dspenc.decode(bytes(out), coefs, len(pcm))
        # C2: full round trip with fresh coefficients
        d2, inf2 = dspenc.encode(pcm); y2 = dspenc.decode(d2, inf2['coefs'], len(pcm))
        ps_ok = stored[0] == c['ps']
        res[f'C nr_name[{i}]'] = dict(frames=nf, stored_frames_reproduced=f'{nsame}/{nf}',
                                      decode_of_reencode_equal=bool(np.array_equal(y1, pcm)),
                                      stored_ps_equals_first_frame=bool(ps_ok),
                                      roundtrip_fresh_coefs_snr_db=round(dspenc.snr_db(pcm, y2), 2),
                                      fresh_coefs=inf2['coefs'], stored_coefs=coefs)
        print(f"C  nr_name[{i}] (sample {1476 + i}): game coefs -> stored frames reproduced {nsame}/{nf}, "
              f"decode identical={np.array_equal(y1, pcm)}; header ps == first frame byte: {ps_ok}; "
              f"fresh-coef round trip SNR {res[f'C nr_name[{i}]']['roundtrip_fresh_coefs_snr_db']} dB")
    json.dump(res, open(os.path.join(HERE, 'out', 'encoder_verification.json'), 'w'), indent=1, default=str)

if __name__ == '__main__':
    main()
