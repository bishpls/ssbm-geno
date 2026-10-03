import struct, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
ROM = open(paths.ROM_PATH, 'rb').read()
LEN = [1]*0xB6 + [2]*10 + [2,2,2,2,1,1,2,1,2,1,1,1,1,2,2,2, 1,2,2,2,2,1,1,1,1,2,2,2,2,2,2,2,
       2,2,2,2,3,3,1,2,3,3,1,1,2,2,1,1, 3,4,2,1,3,1,2,1,1,1,1,1,4,1,1,1]
assert len(LEN) == 256
def parse(kind, idx):
    tab, data = (0x043E26, 0x044226) if kind == 'battle' else (0x042826, 0x042C26)
    chans = []
    for c in range(2):
        p = struct.unpack_from('<H', ROM, tab + idx*4 + c*2)[0]
        if p == 0: chans.append(None); continue
        o = p - 0x3400 + data
        cmds = []
        while True:
            op = ROM[o]; n = LEN[op]
            cmds.append(ROM[o:o+n]); o += n
            if op in (0xD0, 0xCD, 0xCE) or len(cmds) > 400: break
        chans.append((p, cmds))
    return chans
if __name__ == '__main__':
    use = collections.Counter()
    for i in range(256):
        ch = parse('battle', i)
        s = set()
        for c in ch:
            if c:
                for cmd in c[1]:
                    if cmd[0] == 0xDE: s.add(cmd[1])
        for x in s: use[x] += 1
        if any(ch): print(i, [hex(c[0]) if c else None for c in ch], sorted(s))
    print(sorted(use.items()))
