"""Check that every GPU-read buffer in an HSD .dat/.usd file sits on a 32-byte boundary.
    python3 projects/geno/menus/gxalign.py FILE...
The GPU reads textures, palettes, display lists and vertex arrays only from 32-byte boundaries, and HSDRaw re-saves a
loaded file with blocks of 0x40 bytes or less on 4-byte boundaries unless they are flagged. This walks every model
(joints, their meshes and materials, and material animations' image and palette banks) from the file's roots and prints
each misaligned buffer; exit status 1 if any.
"""
import struct, sys

JOBJ_NEXT, JOBJ_CHILD, JOBJ_DOBJ = 0x0C, 0x08, 0x10


class Dat:
    def __init__(self, path):
        b = open(path, 'rb').read()
        self.fsize, self.dsize, self.nrel, self.nroot, self.nref = struct.unpack('>5I', b[:20])
        self.data = b[0x20:0x20 + self.dsize]
        rel = 0x20 + self.dsize
        self.ptrs = set(struct.unpack(f'>{self.nrel}I', b[rel:rel + 4 * self.nrel]))
        rt = rel + 4 * self.nrel
        strt = rt + 8 * (self.nroot + self.nref)
        self.roots = []
        for i in range(self.nroot):
            off, name = struct.unpack('>II', b[rt + 8 * i:rt + 8 * i + 8])
            s = b[strt + name:b.index(b'\0', strt + name)].decode('ascii', 'replace')
            self.roots.append((s, off))

    def p(self, off):
        """The pointer stored at OFF, or None if that word is not relocated (a null or plain value)."""
        if off is None or off + 4 > len(self.data) or off not in self.ptrs: return None
        return struct.unpack('>I', self.data[off:off + 4])[0]

    def u32(self, off): return struct.unpack('>I', self.data[off:off + 4])[0]
    def u16(self, off): return struct.unpack('>H', self.data[off:off + 2])[0]


def check(path):
    d = Dat(path)
    bad, seen, n = [], set(), {'image': 0, 'tlut': 0, 'dlist': 0, 'vtx': 0}

    def buf(kind, at, where):
        if at is None: return
        n[kind] += 1
        if at % 32: bad.append(f'{kind} at 0x{at:X} ({where})')

    def image(o, where):
        if o is None or ('img', o) in seen: return
        seen.add(('img', o)); buf('image', d.p(o), where)

    def tlut(o, where):
        if o is None or ('tl', o) in seen: return
        seen.add(('tl', o)); buf('tlut', d.p(o), where)

    def tobj(o, where):
        while o is not None and ('tobj', o) not in seen:
            seen.add(('tobj', o))
            image(d.p(o + 0x4C), where); tlut(d.p(o + 0x50), where)
            o = d.p(o + 0x04)

    def pobj(o, where):
        while o is not None and ('pobj', o) not in seen:
            seen.add(('pobj', o))
            attrs = d.p(o + 0x08)
            while attrs is not None:                                  # GX_VTXATTR list, ended by name 0xFF
                name = d.u32(attrs)
                if name == 0xFF: break
                buf('vtx', d.p(attrs + 0x14), where)
                attrs += 0x18
            buf('dlist', d.p(o + 0x10), where)
            o = d.p(o + 0x04)

    def jobj(o, where):
        while o is not None and ('jobj', o) not in seen:
            seen.add(('jobj', o))
            flags = d.u32(o + 0x04)
            dob = d.p(o + JOBJ_DOBJ) if not (flags & 0x4020) else None     # SPLINE (0x4000) and PTCL (0x20) use this field otherwise
            while dob is not None:
                mob = d.p(dob + 0x08)
                if mob is not None: tobj(d.p(mob + 0x08), where)
                pobj(d.p(dob + 0x0C), where)
                dob = d.p(dob + 0x04)
            jobj(d.p(o + JOBJ_CHILD), where)
            o = d.p(o + JOBJ_NEXT)

    def texanim(o, where):
        while o is not None and ('ta', o) not in seen:
            seen.add(('ta', o))
            imgs, tls = d.p(o + 0x0C), d.p(o + 0x10)
            ni, nt = struct.unpack('>hh', d.data[o + 0x14:o + 0x18])
            for i in range(ni if imgs is not None else 0): image(d.p(imgs + 4 * i), where)
            for i in range(nt if tls is not None else 0): tlut(d.p(tls + 4 * i), where)
            o = d.p(o)

    def matanimjoint(o, where):
        while o is not None and ('maj', o) not in seen:
            seen.add(('maj', o))
            ma = d.p(o + 0x08)
            while ma is not None and ('ma', ma) not in seen:
                seen.add(('ma', ma)); texanim(d.p(ma + 0x08), where); ma = d.p(ma)
            matanimjoint(d.p(o), where)
            o = d.p(o + 0x04)

    def model_desc(o, where):                                         # JOBJDesc: joint, anim[], matanim[], shapeanim[]
        jobj(d.p(o), where)
        arr = d.p(o + 0x08)
        while arr is not None and d.p(arr) is not None:
            matanimjoint(d.p(arr), where); arr += 4

    for name, off in d.roots:
        if name.endswith('matanim_joint'): matanimjoint(off, name)
        elif name.endswith('_joint') and not name.endswith('anim_joint'): jobj(off, name)
        elif name.endswith('_scene_models') or name in ('Stc_rarwmdls', 'Stc_scemdls', 'lupe', 'tdsce'):
            a = off
            while d.p(a) is not None: model_desc(d.p(a), name); a += 4
        elif name.endswith('scene_data') or name in ('pnlsce', 'flmsce'):
            a = d.p(off)
            while a is not None and d.p(a) is not None: model_desc(d.p(a), name); a += 4
        elif name.startswith('ftDataKirbyCopy'):                       # a Kirby copy hat (KirbyHatStruct +0: its joint)
            jobj(d.p(off), name + '.hat_joint')
        elif name.startswith('ftData'):                                # a fighter's metal model (ftData+0x5C)
            jobj(d.p(off + 0x5C), name + '.MetalModel')
        elif name == 'MnSelectChrDataTable':
            for k in range(0x10, 0xA0, 0x10):                         # nine (joint, anim, matanim, shapeanim) models
                jobj(d.p(off + k), name); matanimjoint(d.p(off + k + 8), name)
    print(f'{path}: {n}, {len(bad)} misaligned')
    for b in bad[:20]: print('   ', b)
    return not bad


if __name__ == '__main__':
    ok = all([check(p) for p in sys.argv[1:]])
    sys.exit(0 if ok else 1)
