"""Geno's bank (bank 55) past round 4: the sounds after 550052, appended to geno.ssm and to both smash2.sem.

  550053 GENO_CROWD_CHANT   the crowd's "Ge-no! Ge-no!" (16 kHz, like every retail chant, in the fighter's own bank: Mario's
                            180000 is mario.ssm's sample 0, Kirby's 140000 kirby.ssm's, ...), with the retail chant script
                            `01 smp | FD smp | 10 0A | FD 0A | 06 CC | FD CC | 04 0E | FD 0E | 0E`
  550054 GENO_TIMED_HIT     SMRPG's timed-hit sound (ROM 172), and
  550055 GENO_TIMED_BOOST   SMRPG's timed-special sound cut short (ROM 078); both from projects/geno/sound/timed.py
                            (timed.json), 32 kHz, with Geno's script shape `01 smp | FD smp | 10 aux | 04 prio | 06 vol | 0E`
  550056-550058             the gun normals' sounds fitted to their moves (projects/geno/sound/gunfit.py: the Hand Gun,
                            Hand Cannon and Star Gun cut short). gunfit.json lists the timed sounds and these, so it is
                            the default list when it exists: a rebuild with timed.json alone would drop them

The first 53 entries (550000-550052, sfxbank round 4) and their scripts are kept byte for byte; whatever followed them on
the disc (an earlier build of this) is dropped and the list above is appended in order. So the ids are fixed and a new
chant pick only swaps a sample: rerun with the new WAV.

Reads the bank and sems (default: the disc at $MELEE_DISC), never writes them; writes geno.ssm, smash2_us.sem,
smash2_jp.sem and report.json to OUT (default $CROWD_WORK/out).
    .venv/bin/python projects/geno/sound/cheer/bank.py CHANT.wav [TIMED.json] [--out DIR]
    .venv/bin/python projects/geno/sound/cheer/bank.py --install DIR      # copy OUT's files into $MELEE_DISC (sha1-checked)
"""
import argparse, hashlib, json, os, shutil, struct, sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ssmfile as S  # noqa: E402
from ssmfile import dspadpcm  # noqa: E402

BANK = 55
SFX_BASE = BANK * 10000
ROUND4 = 53                      # 550000-550052: sfxbank round 4 (the installed bank), kept byte for byte
BOOKED = 393216                  # LBAX_GENO_BYTES in the decomp (384 KiB): the ARAM the loader books for geno.ssm, >= data_len
BUDGET = 586208                  # the 4th-largest fighter bank (Kirby): under it the ARAM layout is unchanged
CHANT_SCRIPT = [(0x01, None), (0xFD, None), (0x10, 0x0A), (0xFD, 0x0A), (0x06, 0xCC), (0xFD, 0xCC), (0x04, 0x0E),
                (0xFD, 0x0E), (0x0E, 0)]  # Kirby's (and 21 other chants'); None = the sample id
WORK = os.path.expanduser(os.environ.get('CROWD_WORK', '~/games/melee/work/crowd'))
DISC = os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc'))
SFXBANK = os.path.expanduser(os.environ.get('SFXBANK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'sfxbank')))
TIMED = os.path.join(SFXBANK, 'timed', 'timed.json')
GUNFIT = os.path.join(SFXBANK, 'gunfit', 'gunfit.json')     # timed.json's entries, then 550056-58
if os.path.exists(GUNFIT):
    TIMED = GUNFIT
FILES = {'geno.ssm': ['files/audio/us/geno.ssm', 'files/audio/geno.ssm'],
         'smash2_us.sem': ['files/audio/us/smash2.sem'], 'smash2_jp.sem': ['files/audio/smash2.sem']}


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def script(cmds, sample_id):
    return b''.join(struct.pack('>I', (op << 24) | (sample_id if v is None else v)) for op, v in cmds)


def geno_script(vol, prio, aux):
    return [(0x01, None), (0xFD, None), (0x10, aux), (0x04, prio), (0x06, vol), (0x0E, 0)]


def extras(chant_wav, timed_json):
    """[(sound id, name, int16 pcm, rate, script commands)] in id order."""
    x, sr = sf.read(chant_wav, dtype='int16')
    assert sr == 16000 and x.ndim == 1, (sr, x.shape)
    out = [(SFX_BASE + ROUND4, 'GENO_CROWD_CHANT', x, sr, CHANT_SCRIPT, os.path.abspath(chant_wav))]
    if timed_json:
        for m in json.load(open(timed_json)):
            y, r = sf.read(m['wav'], dtype='int16')
            assert r == m['rate'] and y.ndim == 1
            out.append((m['sound_id'], m['name'], y, r, geno_script(m['vol'], m['prio'], m['aux']), m['wav']))
    assert [e[0] for e in out] == list(range(SFX_BASE + ROUND4, SFX_BASE + ROUND4 + len(out))), 'ids must follow 550052'
    return out


def build(chant_wav, timed_json, out):
    src = {k: open(os.path.join(DISC, v[0]), 'rb').read() for k, v in FILES.items()}
    assert src['geno.ssm'] == open(os.path.join(DISC, FILES['geno.ssm'][1]), 'rb').read(), 'US and JP geno.ssm differ'
    bank = S.parse_ssm(src['geno.ssm'])
    assert bank['count'] >= ROUND4
    ex = extras(chant_wav, timed_json)

    # ---- the bank: entries 0..52 and their data byte for byte, then each new sound at a 32-byte boundary
    last = bank['entries'][ROUND4 - 1]['ch'][0]
    used = (last['cur'] - 2) // 2 + 8 * -(-S.entry_samples(last) // 14)
    recs = [src['geno.ssm'][0x10 + 0x48 * i:0x10 + 0x48 * (i + 1)] for i in range(ROUND4)]
    data = bytearray(bank['data'][:used])
    enc = []
    for sid, name, pcm, rate, cmds, wav in ex:
        B = S.align(len(data)); data += b'\0' * (B - len(data))
        adpcm, info = dspadpcm.encode(pcm)
        recs.append(S.entry_record(rate, B, info))
        data += adpcm
        enc.append((adpcm, info, B))
    geno = S.write_ssm(bank['base'], recs, bytes(data))
    nb = S.parse_ssm(geno)
    assert nb['dlen'] <= BOOKED <= BUDGET, (nb['dlen'], BOOKED)
    kept_records = all(nb['entries'][i]['ch'][0]['raw'] == bank['entries'][i]['ch'][0]['raw'] for i in range(ROUND4))
    kept_data = nb['data'][:used] == bank['data'][:used]
    kept_decode = all(np.array_equal(S.decode_entry(nb, i), S.decode_entry(bank, i)) for i in range(ROUND4))
    rows = []
    for k, ((sid, name, pcm, rate, cmds, wav), (adpcm, info, B)) in enumerate(zip(ex, enc)):
        e = ROUND4 + k
        dec = S.decode_entry(nb, e)
        assert np.array_equal(dec, dspadpcm.decode(adpcm, info['coefs'], len(pcm))) and nb['entries'][e]['rate'] == rate
        rows.append(dict(sound_id=sid, name=name, entry=e, sample_id=bank['base'] + e, rate=rate, samples=len(pcm),
                         seconds=round(len(pcm) / rate, 3), adpcm_bytes=len(adpcm), data_start_byte=B,
                         adpcm_snr_db=round(float(dspadpcm.snr_db(pcm, dec)), 2), wav=wav, wav_sha1=sha1(open(wav, 'rb').read()),
                         script=' '.join(f'{op:02X}:{(bank["base"] + e) if v is None else v:X}' for op, v in cmds)))
    assert kept_records and kept_data and kept_decode

    # ---- the sems: bank 55 is the last bank, so its scripts end the file: keep 53, append ours
    rep_sem, outs = {}, {'geno.ssm': geno}
    for tag in ('smash2_us.sem', 'smash2_jp.sem'):
        sem = S.parse_sem(src[tag])
        assert sem['nb'] == BANK + 1 and S.write_sem(sem['first'], sem['scripts']) == src[tag], 'unexpected sem layout'
        keep = sem['first'][BANK] + ROUND4
        assert sem['ns'] >= keep
        scripts = sem['scripts'][:keep] + [script(cmds, bank['base'] + ROUND4 + k) for k, (_, _, _, _, cmds, _) in enumerate(ex)]
        new = S.write_sem(sem['first'], scripts)
        ns = S.parse_sem(new)
        for k, r in enumerate(rows):
            i = S.resolve(ns, r['sound_id'])
            assert i is not None and S.script_cmds(ns['scripts'][i])[0] == (0x01, r['sample_id']), (tag, r['name'])
        assert ns['scripts'][:keep] == sem['scripts'][:keep] and ns['first'] == sem['first']
        outs[tag] = new
        rep_sem[tag] = dict(scripts=[sem['ns'], ns['ns']], size=len(new), sha1=sha1(new), kept_scripts_identical=True)
    os.makedirs(out, exist_ok=True)
    for name, b in outs.items():
        open(os.path.join(out, name), 'wb').write(b)
    rep = dict(sounds=rows, bank_in_sha1=sha1(src['geno.ssm']), bank_out_sha1=sha1(geno), count=[bank['count'], nb['count']],
               data_len=[bank['dlen'], nb['dlen']], booked=BOOKED, booked_left=BOOKED - nb['dlen'], budget=BUDGET,
               size=len(geno), round4_records_identical=kept_records, round4_data_identical=kept_data,
               round4_decode_identical=kept_decode, sems=rep_sem, inputs={k: sha1(v) for k, v in src.items()})
    json.dump(rep, open(os.path.join(out, 'report.json'), 'w'), indent=1)
    return rep


def install(out):
    """Copy OUT's files over the disc's (US and JP geno.ssm, both sems), backing the originals up once to OUT/orig/."""
    rep = json.load(open(os.path.join(out, 'report.json')))
    want = {'geno.ssm': rep['bank_out_sha1'], 'smash2_us.sem': rep['sems']['smash2_us.sem']['sha1'],
            'smash2_jp.sem': rep['sems']['smash2_jp.sem']['sha1']}
    for name, dests in FILES.items():
        b = open(os.path.join(out, name), 'rb').read()
        assert sha1(b) == want[name], name
        for d in dests:
            p = os.path.join(DISC, d)
            cur = open(p, 'rb').read()
            if sha1(cur) == want[name]:
                continue
            bk = os.path.join(out, 'orig', d)
            if not os.path.exists(bk):
                os.makedirs(os.path.dirname(bk), exist_ok=True); shutil.copy2(p, bk)
            shutil.copyfile(os.path.join(out, name), p)
            assert sha1(open(p, 'rb').read()) == want[name]
            print('installed', p)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('chant', nargs='?')
    ap.add_argument('timed', nargs='?', default=TIMED)
    ap.add_argument('--out', default=os.path.join(WORK, 'out'))
    ap.add_argument('--install', metavar='DIR')
    a = ap.parse_args()
    if a.install:
        install(a.install)
    else:
        r = build(a.chant, a.timed if a.timed and os.path.exists(a.timed) else None, a.out)
        for s in r['sounds']:
            print(f"{s['sound_id']} {s['name']:18s} entry {s['entry']} sample {s['sample_id']} {s['rate']} Hz {s['seconds']:.3f} s "
                  f"{s['adpcm_bytes']} B SNR {s['adpcm_snr_db']} dB  {s['script']}")
        print(f"geno.ssm: {r['count'][0]} -> {r['count'][1]} entries, data_len {r['data_len'][0]} -> {r['data_len'][1]} "
              f"(booked {r['booked']}, {r['booked_left']} left); sems {[v['scripts'] for v in r['sems'].values()]}")
