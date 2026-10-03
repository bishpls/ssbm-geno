"""Apply the ♡♪ font patch to a decomp tree (idempotent), every change inside #ifndef MUST_MATCH:
  - sysdolphin/baselib/sislib_font.h: the tables' sizes from SISLIB_GLYPH_COUNT (287 matching, 289 with ♡ ♪);
  - sysdolphin/baselib/sislib_font.c: the atlas appends sislib_font_geno.inc (font_glyphs.py --decomp writes it);
  - sysdolphin/baselib/hsd_3A76.c: two lookup rows appended before each table's padding row (Shift-JIS 83 BB ♡ -> glyph
    code 0x211F, 81 F4 ♪ -> 0x2120) and the new glyphs' side bearings (the widths table's unused row 287, then 288);
    the byte-size asserts stay for the matching build;
  - melee/mn/mnnamenew.c: the US keyboard's third row gains ♡ (key 17, column 7) and ♪ (key 12, column 8) on two of its
    four blank keys.
Existing glyphs, codes and keys are untouched: the patch only appends, or fills a padding row no glyph used.
    .venv/bin/python projects/geno/trailer/lab/font_patch.py DECOMP
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TAG = 'trailer lab: heart and note glyphs'


def edit(path, fn, binary=False):
    s = open(path, 'rb').read()
    if TAG.encode() in s:
        print('already patched:', path); return
    t = fn(s)
    assert t != s, path
    open(path, 'wb').write(t)
    print('patched:', path)


def header(s):
    s = s.decode()
    old = ('/* 40C680 */ extern SisGlyphCode HSD_SisLib_8040C680[288];\n'
           '/* 40C8C0 */ extern SjisChar lbl_8040C8C0[288];\n'
           '/* 40CB00 */ extern TextGlyphMetrics HSD_SisLib_8040CB00[288];\n'
           '/* 40CD40 */ extern TextGlyphTexture HSD_SisLib_FontAtlas[287];\n')
    new = ('#ifndef MUST_MATCH /* ' + TAG + ' (projects/geno/trailer/lab/font_patch.py): two glyphs appended */\n'
           '#define SISLIB_GLYPH_COUNT 289\n#else\n#define SISLIB_GLYPH_COUNT 287\n#endif\n\n'
           '/* 40C680 */ extern SisGlyphCode HSD_SisLib_8040C680[SISLIB_GLYPH_COUNT + 1];\n'
           '/* 40C8C0 */ extern SjisChar lbl_8040C8C0[SISLIB_GLYPH_COUNT + 1];\n'
           '/* 40CB00 */ extern TextGlyphMetrics HSD_SisLib_8040CB00[SISLIB_GLYPH_COUNT + 1];\n'
           '/* 40CD40 */ extern TextGlyphTexture HSD_SisLib_FontAtlas[SISLIB_GLYPH_COUNT];\n')
    assert s.count(old) == 1
    return s.replace(old, new).encode()


def atlas(s):
    s = s.decode()
    old = '#include <sysdolphin/baselib/sislib_font.inc>\n'
    new = old + '#ifndef MUST_MATCH /* ' + TAG + ': glyphs 287 and 288 */\n#include <sysdolphin/baselib/sislib_font_geno.inc>\n#endif\n'
    assert s.count(old) == 1
    return s.replace(old, new).encode()


def tables(bearings):
    def fn(s):
        s = s.decode()
        rep = [
            ('SisGlyphCode HSD_SisLib_8040C680[288] = {', 'SisGlyphCode HSD_SisLib_8040C680[SISLIB_GLYPH_COUNT + 1] = {'),
            ('    { 0x21, 0x1A }, { 0x21, 0x14 }, { 0x21, 0x0D }, { 0x00, 0x00 },\n};\nSTATIC_ASSERT(sizeof(HSD_SisLib_8040C680) == 0x240);',
             '    { 0x21, 0x1A }, { 0x21, 0x14 }, { 0x21, 0x0D },\n#ifndef MUST_MATCH /* ' + TAG + ' */\n'
             '    { 0x21, 0x1F }, { 0x21, 0x20 },\n#endif\n    { 0x00, 0x00 },\n};\n#ifdef MUST_MATCH\n'
             'STATIC_ASSERT(sizeof(HSD_SisLib_8040C680) == 0x240);\n#endif'),
            ('SjisChar lbl_8040C8C0[288] = {', 'SjisChar lbl_8040C8C0[SISLIB_GLYPH_COUNT + 1] = {'),
            ('    { 0x94, 0xAD }, { 0x90, 0xB6 }, { 0x8D, 0x9E }, { 0x00, 0x00 },\n};\nSTATIC_ASSERT(sizeof(lbl_8040C8C0) == 0x240);',
             '    { 0x94, 0xAD }, { 0x90, 0xB6 }, { 0x8D, 0x9E },\n#ifndef MUST_MATCH /* ' + TAG + ': 83 BB the heart (Shift_JIS-2004), 81 F4 the note */\n'
             '    { 0x83, 0xBB }, { 0x81, 0xF4 },\n#endif\n    { 0x00, 0x00 },\n};\n#ifdef MUST_MATCH\n'
             'STATIC_ASSERT(sizeof(lbl_8040C8C0) == 0x240);\n#endif'),
            ('TextGlyphMetrics HSD_SisLib_8040CB00[288] = {', 'TextGlyphMetrics HSD_SisLib_8040CB00[SISLIB_GLYPH_COUNT + 1] = {'),
            ('    { 0x01, 0x02 }, { 0x00, 0x00 }, { 0x01, 0x01 }, { 0x00, 0x00 },\n};\nSTATIC_ASSERT(sizeof(HSD_SisLib_8040CB00) == 0x240);',
             '    { 0x01, 0x02 }, { 0x00, 0x00 }, { 0x01, 0x01 },\n#ifndef MUST_MATCH /* ' + TAG + ': row 287 held no glyph */\n'
             f'    {{ 0x{bearings[0][0]:02X}, 0x{bearings[0][1]:02X} }}, {{ 0x{bearings[1][0]:02X}, 0x{bearings[1][1]:02X} }},\n'
             '#endif\n    { 0x00, 0x00 },\n};\n#ifdef MUST_MATCH\nSTATIC_ASSERT(sizeof(HSD_SisLib_8040CB00) == 0x240);\n#endif'),
        ]
        for old, new in rep:
            assert s.count(old) == 1, old
            s = s.replace(old, new)
        return s.encode()
    return fn


def keys(s):
    """the US key map's second line (keys 10-19: H R _ 6 & G Q _ 5 %): the blanks become ♪ (key 12) and ♡ (key 17)"""
    i = s.index(b'static MnNameNewKeyMap mnNameNew_KeyMap')
    lines = s[i:].split(b'\n')
    k = 13                                           # the struct's 14th line: mode 2, keys 10-19
    line = lines[k]
    assert line.startswith(b'      "\\x82g", "\\x82q", "\\x81@"') or line.count(b'"\x81@"') == 2, line
    assert line.count(b'"\x81@"') == 2, line
    a = line.replace(b'"\x81@"', b'"\\x81\\xF4"', 1).replace(b'"\x81@"', b'"\\x83\\xBB"', 1)
    new = (b'#ifdef MUST_MATCH\n' + line + b'\n#else /* ' + TAG.encode() + b': keys 12 (the note) and 17 (the heart) */\n' + a + b'\n#endif')
    lines[k] = new
    return s[:i] + b'\n'.join(lines)


def main():
    d = sys.argv[1]
    sys.path.insert(0, HERE)
    import font_glyphs
    gl = [f() for _, f in font_glyphs.GLYPHS]
    b = [font_glyphs.bearings(g) for g in gl]
    subprocess.run([sys.executable, os.path.join(HERE, 'font_glyphs.py'), '--decomp', d], check=True)
    base = os.path.join(d, 'src')
    edit(os.path.join(base, 'sysdolphin/baselib/sislib_font.h'), header)
    edit(os.path.join(base, 'sysdolphin/baselib/sislib_font.c'), atlas)
    edit(os.path.join(base, 'sysdolphin/baselib/hsd_3A76.c'), tables(b))
    edit(os.path.join(base, 'melee/mn/mnnamenew.c'), keys)


if __name__ == '__main__':
    main()
