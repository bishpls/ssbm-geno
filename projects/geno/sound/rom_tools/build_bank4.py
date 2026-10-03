"""Round 4: bank 55 = the 28 round-3 sounds (550000-550027, byte-identical) + Geno's synthesized movement sounds appended
as 550028+ (from ~/animation-pipeline-geno-sound/projects/geno/sound/synth.py -> synth/wav + synth/sounds4.json).

Writes out4/: geno.ssm, smash2_us.sem, smash2_jp.sem, bank_report.json, geno_sfx_ids.json, lbaudio_ax_geno_round4.patch.
Reads the disc and install.sh's backups, never writes them. Per-sample rates (the new sounds are 22050 / 16000 Hz, as
Melee's own footsteps are 16 kHz); the round-3 entries stay 32 kHz.
"""
import os, sys, json, struct, hashlib, subprocess, tempfile
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'announcer', 'tools'))   # dspenc, ssm
import numpy as np, soundfile as sf
import dspenc, ssm
from build_bank import parse_sem, patch_sem, script, sha1, align, BASE_SAMPLE, SFX_BASE, VGM

HERE = os.path.expanduser(os.environ.get('SFXBANK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'sfxbank')))   # the bank's work folder (game audio: outside the repo)
OUT3, OUT4 = os.path.join(HERE, 'out'), os.path.join(HERE, 'out4')
SYNTH = os.path.join(HERE, 'synth')
DISC = os.path.join(os.path.expanduser(os.environ.get('MELEE_DISC', '~/games/melee/disc')), 'files', 'audio')
BACKUP = os.path.join(os.path.expanduser(os.environ.get('MELEE_WORK', '~/games/melee/work')), 'orig', 'audio')
BOOKED = 327680                           # LBAX_GENO_BYTES: the ARAM the DOL books for geno.ssm (data_len must fit)
BUDGET = 586208
R3_SHA1 = '3018694538b51f3da8f359a93a4b17eec8de0883'
RETAIL = {'us': '169b94078cba0f1da66c6a3947a080b971085ceb', 'jp': '12e17f7c54ee0ff005aeed8b7993663c6bdc27bd'}
R3_SEM = {'us': '571d5c743f435877ee561a944cc05c22c42e99d6', 'jp': '752031abfbe593b1a72d37293a5c30f2f5e6e71e'}


def build_ssm(entries):
    """entries: [(pcm int16, rate)]. Same layout as round 3 (build_bank.build_ssm), with a per-entry rate."""
    enc = [dspenc.encode(p) for p, _ in entries]
    count = len(entries); hlen = count * 0x48
    data_off = align(0x10 + hlen, 0x20)
    data = bytearray(); table = bytearray(); spans = []
    for (adpcm, info), (p, rate) in zip(enc, entries):
        B = len(data); assert B % 8 == 0
        start = 2 * B + 2; end = 2 * B + dspenc.nibbles_for(len(p)) - 1
        table += struct.pack('>II', 1, rate)
        table += struct.pack('>HHIII', 0, 0, start, end, start)
        table += struct.pack('>16h', *[v for c in info['coefs'] for v in c])
        table += struct.pack('>HHhhHhhH', 0, info['ps'], 0, 0, 0, 0, 0, 0)
        spans.append((B, len(adpcm))); data += adpcm
    dlen = align(len(data), 0x20); data += b'\0' * (dlen - len(data))
    f = struct.pack('>4I', hlen, dlen, count, BASE_SAMPLE) + table
    f += b'\0' * (data_off - len(f)) + data
    return bytes(f), enc, spans


def vgm_decode(path, subsong):
    with tempfile.TemporaryDirectory() as d:
        o = os.path.join(d, 'x.wav')
        subprocess.run([VGM, '-i', '-s', str(subsong), '-o', o, path], check=True, capture_output=True)
        x, sr = sf.read(o, dtype='int16')
    return x, sr


def main():
    r3 = json.load(open(os.path.join(HERE, 'build', 'sounds.json')))
    new = json.load(open(os.path.join(SYNTH, 'sounds4.json')))
    assert [m['k'] for m in r3] == list(range(28)) and [m['k'] for m in new] == list(range(28, 28 + len(new)))
    entries, meta = [], []
    for m in r3:
        x, sr = sf.read(os.path.join(HERE, 'build', m['file']), dtype='int16'); assert sr == 32000
        entries.append((x, sr)); meta.append(dict(m, rate=32000, src='round3'))
    for m in new:
        x, sr = sf.read(os.path.join(SYNTH, 'wav', m['file']), dtype='int16'); assert sr == m['rate']
        entries.append((x, sr)); meta.append(dict(m, src='synth'))
    geno, enc, spans = build_ssm(entries)
    os.makedirs(OUT4, exist_ok=True)
    open(os.path.join(OUT4, 'geno.ssm'), 'wb').write(geno)
    rep = dict(geno_ssm=dict(size=len(geno), sha1=sha1(geno)))

    # ---- round 3 kept exactly: the 28 table records and their ADPCM bytes are identical to the installed round-3 file
    g3 = open(os.path.join(OUT3, 'geno.ssm'), 'rb').read()
    if sha1(g3) != R3_SHA1:   # a fresh SNES capture renders a hair differently (README): checked only with BANK_STRICT=1
        assert not os.environ.get('BANK_STRICT'), 'round 3 differs from the reference build'
        print(f'note: round 3 geno.ssm {sha1(g3)[:12]} is not the reference build ({R3_SHA1[:12]}): a fresh capture')
    b3, b4 = ssm.parse(os.path.join(OUT3, 'geno.ssm')), ssm.parse(os.path.join(OUT4, 'geno.ssm'))
    rec3 = g3[0x10:0x10 + 28 * 0x48]; rec4 = geno[0x10:0x10 + 28 * 0x48]
    used3 = spans[27][0] + spans[27][1]
    same_records = rec3 == rec4
    same_adpcm = g3[b3['data_off']:b3['data_off'] + used3] == geno[b4['data_off']:b4['data_off'] + used3]
    assert same_records and same_adpcm, 'round-3 entries changed'
    rep['round3_kept'] = dict(table_records_identical=same_records, adpcm_bytes_identical=same_adpcm, adpcm_bytes=used3)

    # ---- sems: retail + 28 round-3 scripts + the new ones; the first 28 identical to round 3's
    scripts = [script(BASE_SAMPLE + m['k'], m['vol'], m['prio'], m['aux']) for m in meta]
    for tag, rel in (('us', 'us/smash2.sem'), ('jp', 'smash2.sem')):
        src = next(p for p in (os.path.join(DISC, rel), os.path.join(BACKUP, rel))
                   if os.path.exists(p) and sha1(open(p, 'rb').read()) == RETAIL[tag])
        orig = open(src, 'rb').read()
        sem = patch_sem(orig, scripts)
        open(os.path.join(OUT4, f'smash2_{tag}.sem'), 'wb').write(sem)
        r3sem = open(os.path.join(OUT3, f'smash2_{tag}.sem'), 'rb').read(); assert sha1(r3sem) == R3_SEM[tag]
        so, s3, s4 = parse_sem(orig), parse_sem(r3sem), parse_sem(sem)
        resolved = []
        for m in meta:
            bank, mem = divmod(SFX_BASE + m['k'], 10000); idx = s4['first'][bank] + mem
            sc = s4['scripts'][idx]; resolved.append(int.from_bytes(sc[1:4], 'big') == BASE_SAMPLE + m['k'])
        rep[f'smash2_{tag}'] = dict(
            source=src, size=len(sem), sha1=sha1(sem), banks=[so['nb'], s4['nb']], scripts=[so['ns'], s4['ns']],
            first_script_55=s4['first'][55],
            retail_scripts_identical=all(a == c for a, c in zip(so['scripts'], s4['scripts'][:so['ns']])),
            retail_first_script_identical=s4['first'][:55] == so['first'],
            round3_geno_scripts_identical=s4['scripts'][so['ns']:so['ns'] + 28] == s3['scripts'][so['ns']:so['ns'] + 28],
            sound_ids_resolve_to_samples=all(resolved))
        assert all(v for k, v in rep[f'smash2_{tag}'].items() if k.endswith(('identical', 'samples')))

    # ---- verify the bank round trip
    b = b4
    assert b['count'] == len(meta) and b['start'] == BASE_SAMPLE and b['dlen'] <= BOOKED and b['dlen'] % 32 == 0
    rows = []
    for m, s, (adpcm, info), (p, rate) in zip(meta, b['sounds'], enc, entries):
        c = s['chans'][0]
        ours = ssm.decode_channel(b, c)
        same = np.array_equal(ours, dspenc.decode(adpcm, info['coefs'], len(p))) and len(ours) == len(p)
        v, vsr = vgm_decode(os.path.join(OUT4, 'geno.ssm'), s['index'] + 1)
        n = min(len(v), len(ours))
        rows.append(dict(k=m['k'], name=m['name'], sound_id=SFX_BASE + m['k'], sample_id=BASE_SAMPLE + m['k'], rate=s['rate'],
                         samples=len(p), dur=round(len(p) / rate, 3), adpcm_bytes=len(adpcm), decode_equals_encoder=bool(same),
                         snr_db=round(dspenc.snr_db(p, ours), 2), vgmstream_rate=vsr, vgmstream_bit_exact=bool(np.array_equal(v[:n], ours[:n]))))
        if m['src'] == 'synth':
            os.makedirs(os.path.join(SYNTH, 'decoded'), exist_ok=True)
            sf.write(os.path.join(SYNTH, 'decoded', m['file']), ours, rate, subtype='PCM_16')
    new_bytes = sum(r['adpcm_bytes'] for r in rows[28:])
    rep['geno_ssm'].update(count=b['count'], base_sample=b['start'], data_off=hex(b['data_off']), data_len=b['dlen'],
                           round3_data_len=b3['dlen'], new_adpcm_bytes=new_bytes, booked=BOOKED, booked_left=BOOKED - b['dlen'],
                           budget=BUDGET, samples=rows)
    assert all(r['decode_equals_encoder'] and r['vgmstream_bit_exact'] and r['vgmstream_rate'] == r['rate'] for r in rows)
    json.dump(rep, open(os.path.join(OUT4, 'bank_report.json'), 'w'), indent=1)

    # ---- the id table (round 3's entries carried over, the new ones with their use and script)
    ids3_p = os.path.join(OUT3, 'geno_sfx_ids.json')     # round 3's id table (names, uses, scripts), kept in the repo too
    ids3 = json.load(open(ids3_p if os.path.exists(ids3_p) else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geno_sfx_ids_r3.json')))
    ids = ids3 + [dict(sound_id=SFX_BASE + m['k'], hex=hex(SFX_BASE + m['k']), k=m['k'], name=m['name'],
                       sample_id=BASE_SAMPLE + m['k'], rate=m['rate'], dur_s=m['dur'], adpcm_bytes=r['adpcm_bytes'],
                       use=m['use'], script=dict(vol=m['vol'], prio=m['prio'], aux=m['aux']), seed=m['seed'],
                       source_kind='synthesized from scratch (projects/geno/sound/synth.py)', peak_dbfs=m['peak'],
                       short_lufs=m['short'], max_momentary_lufs=m['lufs'], eff_short_lufs=m['eff_short'],
                       adpcm_snr_db=r['snr_db']) for m, r in zip(meta[28:], rows[28:])]
    json.dump(ids, open(os.path.join(OUT4, 'geno_sfx_ids.json'), 'w'), indent=1)

    # ---- the decomp side: the bank-55 id range grows (lbaudio_ax.c gates Geno's ids by LBAX_GENO_SFX_LAST)
    last = SFX_BASE + len(meta) - 1
    patch = f"""animation-pipeline: round 4 of Geno's bank: sounds 550028-{last} (synthesized movement sounds) follow the 28
round-3 sounds. lbAudioAx_800237A8 and the bank-range table gate Geno's ids with LBAX_GENO_SFX_LAST, so it must cover
them. data_len {b['dlen']} still fits LBAX_GENO_BYTES (327680).

--- a/src/melee/lb/lbaudio_ax.c
+++ b/src/melee/lb/lbaudio_ax.c
@@ -117,7 +117,7 @@
  * The bank count becomes 56, so the spare "no bank" row and sentinel move from 55 to 56. */
 #define LBAX_BANKS 56
 #define LBAX_GENO_SFX_FIRST 550000
-#define LBAX_GENO_SFX_LAST 550027
+#define LBAX_GENO_SFX_LAST {last}
 #define LBAX_GENO_BYTES 327680 /* ARAM the loader books for geno.ssm: a 320 KiB cap, >= its data_len (283104 in the clean-source build) */
 #define LBAX_IS_GENO_SFX(id) ((id) >= LBAX_GENO_SFX_FIRST && (id) <= LBAX_GENO_SFX_LAST)
 #else
"""
    open(os.path.join(OUT4, 'lbaudio_ax_geno_round4.patch'), 'w').write(patch)

    write_install(rep)
    g = rep['geno_ssm']
    print(f"geno.ssm: {g['size']} B sha1 {g['sha1']}; {g['count']} samples from {g['base_sample']}; data_len {g['data_len']} "
          f"(round 3 {g['round3_data_len']}, new ADPCM {new_bytes} B); booked {BOOKED}, left {g['booked_left']}")
    print('  round-3 records + ADPCM identical:', same_records, same_adpcm, '| decode==encoder, vgmstream bit-exact, rates:',
          all(r['decode_equals_encoder'] for r in rows), all(r['vgmstream_bit_exact'] for r in rows),
          sorted(set(r['vgmstream_rate'] for r in rows)))
    print('  new SNR dB min/median %.1f/%.1f' % (min(r['snr_db'] for r in rows[28:]), np.median([r['snr_db'] for r in rows[28:]])))
    for tag in ('us', 'jp'):
        r = rep[f'smash2_{tag}']
        print(f"smash2_{tag}.sem: {r['size']} B sha1 {r['sha1']}; banks {r['banks']} scripts {r['scripts']} first[55]={r['first_script_55']}")
    print('LBAX_GENO_SFX_LAST ->', last)


INSTALL = r"""#!/bin/sh
# Install Geno's sound bank, round 4 (bank 55): the 28 round-3 sounds (550000-550027, byte-identical) plus the synthesized
# movement sounds 550028-@LAST@, in both language folders, and the two patched smash2.sem files.
#   sh install.sh            install round 4 (backs up the retail sems once, if that has not happened yet)
#   sh install.sh --round3   go back to round 3 (../out: the 28-sound bank and its sems)
#   sh install.sh --restore  put the retail sems back and remove geno.ssm
# Accepted previous states: retail, or any earlier Geno round (the round-3 files are what the disc holds now).
# Needs the matching DOL: lbaudio_ax_bank55.patch + lbaudio_ax_geno_bytes.patch + lbaudio_ax_geno_round4.patch
# (LBAX_GENO_SFX_LAST = @LAST@); with an older DOL the new ids are gated off and the old ones still play.
# Every file is checked by SHA-1 before and after copying; nothing unknown is overwritten.
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
R3="$HERE/../out"
AUD="${MELEE_DISC:-$HOME/games/melee/disc}/files/audio"
BAK="${MELEE_WORK:-$HOME/games/melee/work}/orig/audio"
US_SEM_ORIG=169b94078cba0f1da66c6a3947a080b971085ceb      # retail audio/us/smash2.sem (132,184 B)
JP_SEM_ORIG=12e17f7c54ee0ff005aeed8b7993663c6bdc27bd      # retail audio/smash2.sem (132,364 B)
GENO4=@GENO4@
US4=@US4@
JP4=@JP4@
GENO3=3018694538b51f3da8f359a93a4b17eec8de0883            # round 3 (ROM captures)
US3=571d5c743f435877ee561a944cc05c22c42e99d6              # rounds 1-3 sems (28 Geno scripts)
JP3=752031abfbe593b1a72d37293a5c30f2f5e6e71e
GENO_OLD="d4cadd27d9fcb648bdbb2b8d6d8e66599e51f1c4 562f5e0c026010aac07330431232aae9cf2289cd $GENO3 $GENO4"
US_OLD="$US3 $US4"; JP_OLD="$JP3 $JP4"

sha1() { shasum -a 1 "$1" | cut -d' ' -f1; }
need() { [ -f "$1" ] && [ "$(sha1 "$1")" = "$2" ] || { echo "$1: missing or wrong SHA-1" >&2; exit 1; }; }
known() { _c="$1"; shift; for _k in "$@"; do [ "$_c" = "$_k" ] && return 0; done; return 1; }   # (sh: no locals)
precheck() {  # refuse before copying anything if a target is unknown
    for g in "$AUD/geno.ssm" "$AUD/us/geno.ssm"; do
        if [ -f "$g" ]; then known "$(sha1 "$g")" $GENO_OLD || { echo "$g exists and is not a known Geno build; refusing" >&2; exit 1; }; fi
    done
    known "$(sha1 "$AUD/us/smash2.sem")" $US_SEM_ORIG $US_OLD || { echo "$AUD/us/smash2.sem is neither retail nor a Geno build; refusing" >&2; exit 1; }
    known "$(sha1 "$AUD/smash2.sem")" $JP_SEM_ORIG $JP_OLD || { echo "$AUD/smash2.sem is neither retail nor a Geno build; refusing" >&2; exit 1; }
}

put_sem() {  # $1 disc file, $2 backup, $3 retail sha, $4 new file, $5 new sha, $6.. accepted earlier Geno shas
    sf_="$1"; sb_="$2"; so_="$3"; sn_="$4"; sh_="$5"; shift 5
    scur_="$(sha1 "$sf_")"
    if [ "$scur_" = "$sh_" ]; then echo "already installed: $sf_"; return; fi
    if [ "$scur_" = "$so_" ]; then
        if [ ! -f "$sb_" ]; then mkdir -p "$(dirname "$sb_")"; cp -p "$sf_" "$sb_"; echo "backed up $sf_ -> $sb_"; fi
    elif ! known "$scur_" "$@"; then echo "$sf_ is neither retail nor a Geno build (sha1 $scur_); refusing" >&2; exit 1; fi
    need "$sb_" "$so_"                               # the retail backup must exist before anything is replaced
    cp "$sn_" "$sf_"; need "$sf_" "$sh_"; echo "installed $sf_"
}
put_geno() {  # $1 new file, $2 new sha
    for g in "$AUD/geno.ssm" "$AUD/us/geno.ssm"; do
        if [ -f "$g" ]; then known "$(sha1 "$g")" $GENO_OLD || { echo "$g exists and is not a known Geno build; refusing" >&2; exit 1; }; fi
        cp "$1" "$g"; need "$g" "$2"; echo "installed $g"
    done
}

case "${1:-}" in
--restore)
    need "$BAK/us/smash2.sem" "$US_SEM_ORIG"; need "$BAK/smash2.sem" "$JP_SEM_ORIG"
    for f in "$AUD/us/smash2.sem" "$AUD/smash2.sem"; do
        known "$(sha1 "$f")" $US_SEM_ORIG $JP_SEM_ORIG $US_OLD $JP_OLD || { echo "$f is not retail or a Geno build; refusing" >&2; exit 1; }
    done
    cp -p "$BAK/us/smash2.sem" "$AUD/us/smash2.sem"; cp -p "$BAK/smash2.sem" "$AUD/smash2.sem"
    for g in "$AUD/geno.ssm" "$AUD/us/geno.ssm"; do
        if [ -f "$g" ]; then
            if known "$(sha1 "$g")" $GENO_OLD; then rm "$g"; else echo "left $g in place: not a known Geno build" >&2; fi
        fi
    done
    echo "restored the retail sems; removed geno.ssm" ;;
--round3)
    need "$R3/geno.ssm" "$GENO3"; need "$R3/smash2_us.sem" "$US3"; need "$R3/smash2_jp.sem" "$JP3"; precheck
    put_sem "$AUD/us/smash2.sem" "$BAK/us/smash2.sem" "$US_SEM_ORIG" "$R3/smash2_us.sem" "$US3" $US_OLD
    put_sem "$AUD/smash2.sem" "$BAK/smash2.sem" "$JP_SEM_ORIG" "$R3/smash2_jp.sem" "$JP3" $JP_OLD
    put_geno "$R3/geno.ssm" "$GENO3"
    echo "done: round 3 (sounds 550000-550027)" ;;
"")
    need "$HERE/geno.ssm" "$GENO4"; need "$HERE/smash2_us.sem" "$US4"; need "$HERE/smash2_jp.sem" "$JP4"; precheck
    put_sem "$AUD/us/smash2.sem" "$BAK/us/smash2.sem" "$US_SEM_ORIG" "$HERE/smash2_us.sem" "$US4" $US_OLD
    put_sem "$AUD/smash2.sem" "$BAK/smash2.sem" "$JP_SEM_ORIG" "$HERE/smash2_jp.sem" "$JP4" $JP_OLD
    put_geno "$HERE/geno.ssm" "$GENO4"
    echo "done: round 4, bank 55 (sounds 550000-@LAST@) installed" ;;
*) echo "usage: sh install.sh [--round3 | --restore]" >&2; exit 2 ;;
esac
"""


def write_install(rep):
    last = SFX_BASE + rep['geno_ssm']['count'] - 1
    t = INSTALL.replace('@LAST@', str(last)).replace('@GENO4@', rep['geno_ssm']['sha1']) \
        .replace('@US4@', rep['smash2_us']['sha1']).replace('@JP4@', rep['smash2_jp']['sha1'])
    p = os.path.join(OUT4, 'install.sh'); open(p, 'w').write(t); os.chmod(p, 0o755)


if __name__ == '__main__':
    main()
