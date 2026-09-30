"""Write out/lbaudio_ax_bank55.patch: a git-style unified diff against ~/games/melee/decomp (branch ext) that adds
bank 55 (geno.ssm). Edits a scratch copy only; the decomp is never written. Every behavioural change is under
#ifndef MUST_MATCH: literals become LBAX_BANKS, which is 55 when MUST_MATCH is defined, so the matching build is
unchanged."""
import os, sys, json, subprocess, tempfile, shutil, re

DECOMP = os.path.expanduser('~/games/melee/decomp')
REL = 'src/melee/lb/lbaudio_ax.c'
HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def sub(s, old, new, count=1):
    n = s.count(old)
    assert n == count, f'{n} != {count}: {old!r}'
    return s.replace(old, new)

def main():
    rep = json.load(open(os.path.join(HERE, 'out', 'bank_report.json')))
    nsfx = rep['geno_ssm']['count']; dlen = rep['geno_ssm']['data_len']
    src = open(os.path.join(DECOMP, REL)).read()
    s = src
    # ---- constants, before the state arrays
    s = sub(s, 'static int lbl_804337C4[0x38];\n', f'''#ifndef MUST_MATCH
/* animation-pipeline: bank 55 = geno.ssm, Geno's own sounds (IDs 550000-{550000 + nsfx - 1}, samples 1551-{1551 + nsfx - 1}).
 * The bank count becomes 56, so the spare "no bank" row and sentinel move from 55 to 56. */
#define LBAX_BANKS 56
#define LBAX_GENO_SFX_FIRST 550000
#define LBAX_GENO_SFX_LAST {550000 + nsfx - 1}
#define LBAX_GENO_BYTES {dlen} /* geno.ssm data_len: the ARAM the loader books for it */
#define LBAX_IS_GENO_SFX(id) ((id) >= LBAX_GENO_SFX_FIRST && (id) <= LBAX_GENO_SFX_LAST)
#else
#define LBAX_BANKS 55
#endif

static int lbl_804337C4[LBAX_BANKS + 1];
''')
    for a in ('lbl_804338A4', 'lbl_80433984', 'lbl_80433A64', 'lbl_80433B44'):
        s = sub(s, f'static int {a}[0x38];', f'static int {a}[LBAX_BANKS + 1];')
    # ---- Geno's kind -> bank 55
    s = sub(s, '''#ifndef MUST_MATCH /* animation-pipeline: 0x21 none (no bank), Geno (scaffold: Mario's bank) */
    { 0x37, 0x000000000 }, { 0x12, 0x000040000 },
#endif''', '''#ifndef MUST_MATCH /* animation-pipeline: 0x21 none (no bank), Geno: his own bank 55 (geno.ssm) */
    { 0x37, 0x000000000 }, { 0x37, 0x0080000000000000ULL },
#endif''')
    # ---- per-bank tables: row 55 = geno.ssm, row 56 = the spare/sentinel row
    s = sub(s, 'static s8 s32_arr_803BB5D0[0x38][4] = {', 'static s8 s32_arr_803BB5D0[LBAX_BANKS + 1][4] = {')
    s = sub(s, '''    { 0x06, 0x01, 0x01, 0x00 }, { 0x05, 0x02, 0x02, 0x00 },
    { 0x01, 0x05, 0x05, 0x00 },
};''', f'''    {{ 0x06, 0x01, 0x01, 0x00 }}, {{ 0x05, 0x02, 0x02, 0x00 }},
    {{ 0x01, 0x05, 0x05, 0x00 }},
#ifndef MUST_MATCH
    /* 55 geno.ssm: fighter budget class, load priority 2, eviction class 3, no size variants */
    {{ 0x04, 0x02, 0x03, {nsfx} }},
#endif
}};''')
    s = sub(s, 'static int s32_arr_803BB8D4[0x38][2] = {', 'static int s32_arr_803BB8D4[LBAX_BANKS + 1][2] = {')
    s = sub(s, '''    { 0x83D60, 0x83D60 }, { 0x83D60, 0x83D60 },
};''', '''    { 0x83D60, 0x83D60 },
#ifndef MUST_MATCH
    { LBAX_GENO_SFX_FIRST, LBAX_GENO_SFX_LAST }, /* 55 geno.ssm */
#endif
    { 0x83D60, 0x83D60 },
};''')
    s = sub(s, '''    "1pend.ssm",    "last.ssm",    "end.ssm",      NULL,
};''', '''    "1pend.ssm",    "last.ssm",    "end.ssm",
#ifndef MUST_MATCH
    "geno.ssm", /* 55 */
#endif
    NULL,
};''')
    s = sub(s, '''    1536,    0, 0,      0,
};''', '''    1536,    0,
#ifndef MUST_MATCH
    LBAX_GENO_BYTES, 0, /* 55 geno.ssm */
#endif
    0,       0,
};''')
    # ---- the bank count and the "no bank" sentinel (55 -> LBAX_BANKS)
    s = sub(s, '    if (i >= 55) {\n        return 1;', '    if (i >= LBAX_BANKS) {\n        return 1;')
    s = sub(s, '''    if (arg0 >= 0 && arg0 < 0x83D60) {
        for (i = 0; i < 55; i++) {''', '''#ifndef MUST_MATCH
    if (arg0 >= 0 && (arg0 < 0x83D60 || LBAX_IS_GENO_SFX(arg0))) {
#else
    if (arg0 >= 0 && arg0 < 0x83D60) {
#endif
        for (i = 0; i < LBAX_BANKS; i++) {''')
    s = sub(s, '''        }
    }
    return 55;
}''', '''        }
    }
    return LBAX_BANKS;
}''')
    s = sub(s, '    if (idx >= 0 && idx < 55) {\n        return s32_arr_803BB5D0[idx][3];',
            '    if (idx >= 0 && idx < LBAX_BANKS) {\n        return s32_arr_803BB5D0[idx][3];')
    s = sub(s, '    for (i = 55; i > count; i--) {', '    for (i = LBAX_BANKS; i > count; i--) {')
    s = sub(s, '    bool used[56];', '    bool used[LBAX_BANKS + 1];')
    s = sub(s, '''    for (i = 0; zero = count = 0, i < 56; i++) {
        lbl_80433B44[i] = 55;''', '''    for (i = 0; zero = count = 0, i < LBAX_BANKS + 1; i++) {
        lbl_80433B44[i] = LBAX_BANKS;''')
    s = sub(s, '''    for (; count <= 55; count++) {
        for (index = 0; index <= 55; index++) {''', '''    for (; count <= LBAX_BANKS; count++) {
        for (index = 0; index <= LBAX_BANKS; index++) {''')
    s = sub(s, '                for (k = 0; k < 55; k++) {', '                for (k = 0; k < LBAX_BANKS; k++) {')
    s = sub(s, '&& j < 55; j++)', '&& j < LBAX_BANKS; j++)')
    s = sub(s, '    for (i = 0; i < 56; i++) {\n        lbl_804337C4[i] = -1;', '    for (i = 0; i < LBAX_BANKS + 1; i++) {\n        lbl_804337C4[i] = -1;')
    # the remaining plain bank loops
    n_loops = len(re.findall(r'for \((i|i = count) = 0; i < 55; i\+\+\)', s))
    s = re.sub(r'for \(i = 0; i < 55; i\+\+\)', 'for (i = 0; i < LBAX_BANKS; i++)', s)
    s = sub(s, 'for (i = count = 0; i < 55; i++)', 'for (i = count = 0; i < LBAX_BANKS; i++)')
    assert '< 55;' not in s and '<= 55;' not in s and '[0x38]' not in s, 'a bank literal was missed'
    assert s.count('== 55)') == 1                          # 80026EBC: the stage table's own "no bank" value stays
    # ---- sound-ID gates: let Geno's range through
    s = sub(s, '''int lbAudioAx_800237A8(int id, int vol, int pan)
{
    if (id >= 0x83D61) {''', '''int lbAudioAx_800237A8(int id, int vol, int pan)
{
#ifndef MUST_MATCH
    if (id >= 0x83D61 && !LBAX_IS_GENO_SFX(id)) {
#else
    if (id >= 0x83D61) {
#endif''')
    s = sub(s, '''    if (sfx_id < 0x83D60) {
        params.owner = owner;''', '''#ifndef MUST_MATCH
    if (sfx_id < 0x83D60 || LBAX_IS_GENO_SFX(sfx_id)) {
#else
    if (sfx_id < 0x83D60) {
#endif
        params.owner = owner;''')
    # ---- write a/b trees and diff
    tmp = tempfile.mkdtemp()
    for side, text in (('a', src), ('b', s)):
        p = os.path.join(tmp, side, REL); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(text)
    d = subprocess.run(['diff', '-u', f'a/{REL}', f'b/{REL}'], cwd=tmp, capture_output=True, text=True)
    patch = d.stdout
    head = subprocess.run(['git', '-C', DECOMP, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    header = (f'animation-pipeline: bank 55 (geno.ssm) for Geno\'s sounds, IDs 550000-{550000 + nsfx - 1}.\n'
              f'Base: ~/games/melee/decomp branch ext, HEAD {head} ({REL} unmodified in the working tree).\n'
              f'Behaviour changes only without MUST_MATCH (LBAX_BANKS is 55 with MUST_MATCH, so the matching build is unchanged).\n'
              f'Pair with out/geno.ssm and out/smash2_{{us,jp}}.sem.\n\n')
    out = os.path.join(HERE, 'out', 'lbaudio_ax_bank55.patch')
    open(out, 'w').write(header + patch)
    chk = subprocess.run(['git', '-C', DECOMP, 'apply', '--check', '-v', out], capture_output=True, text=True)
    print(chk.stdout, chk.stderr, 'exit', chk.returncode)
    print(f'{n_loops} plain loops rewritten; patch {out}: {patch.count(chr(10))} lines')
    shutil.rmtree(tmp)

if __name__ == '__main__':
    main()
