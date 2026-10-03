"""Play any SMRPG music track through the game's own SPC700 driver (blargg snes_spc, local log build).

Starts from the attract-demo battle state (driver resident), then does what the S-CPU does to change music
(protocol read from the driver at $0308/$16D9 and the boot port trace):
  $0F stop; $0E ff free music samples; $25 echo (delay, feedback, volume); per header sample: $0D id vol + words
  (loop, gain, tuning, n3, n3) + n3 3-byte packets; $01 n2 + n2 2-byte packets to $2000; $04 play.
Analysis only: the output never leaves ~/games.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'sound', 'capture'))   # spcharness, paths
import numpy as np
import smrpg_seq as S
import spclog as L
import paths  # noqa: E402
SPC_STATE = paths.STATE

class Driver:
    def __init__(self):
        self.s = L.Spc(open(SPC_STATE, 'rb').read())
        self.s.play(int(0.25 * L.SR))
        self.ctr = 0x40
    def wait(self, cond, maxs=0.5):
        n = 0
        while not cond():
            self.s.play(16); n += 16
            if n > maxs * L.SR: raise TimeoutError
    def cmd(self, c, p1=0, p2=0, p3=0, ack=True):
        s = self.s
        s.port(1, p1); s.port(2, p2); s.port(3, p3); s.port(0, c)
        if ack:
            self.wait(lambda: s.rport(0) == 0xFF); s.port(0, 0); self.wait(lambda: s.rport(0) == 0x00)
    def packet(self, p1, p2, p3, c, last=False):
        s = self.s
        s.port(1, p1); s.port(2, p2); s.port(3, p3); s.port(0, c)
        # the last packet's echo is replaced at once by the $FF completion ack
        self.wait(lambda: s.rport(0) == c or (last and s.rport(0) == 0xFF))
    def finish(self):
        self.wait(lambda: self.s.rport(0) == 0xFF); self.s.port(0, 0); self.wait(lambda: self.s.rport(0) == 0x00)
    def sample(self, sid, vol):
        R = S.ROM
        off = S.u24(R, sid * 3 + 0x042333) - 0xC00000
        n = S.u16(R, off); brr = R[off + 2: off + 2 + n]
        loop = S.u16(R, sid * 2 + 0x04248F); gain = S.u16(R, sid * 2 + 0x042577); tune = S.u16(R, sid * 2 + 0x04265F)
        n3 = (n + 2) // 3; brr = brr + bytes(3 * n3 - n)
        s = self.s
        s.port(1, sid); s.port(2, vol); s.port(3, 0); s.port(0, 0x0D)
        self.wait(lambda: s.rport(0) == 0x0D)
        c = 0x0D
        for k, w in enumerate((loop, gain, tune, n3, n3)):
            c += 1; self.packet(0, w & 0xFF, w >> 8, c, last=(k == 2))
            if k == 2 and s.rport(0) == 0xFF:   # already resident: the driver stops after the tuning word
                self.finish(); return 'resident'
        for i in range(n3):
            c = (c + 1) & 0x7F or 1
            self.packet(brr[3*i], brr[3*i+1], brr[3*i+2], c, last=(i == n3 - 1))
        self.finish(); return 'loaded'
    def upload_seq(self, data):
        n2 = (len(data) + 1) // 2; data = data + bytes(2 * n2 - len(data))
        s = self.s
        s.port(1, 0); s.port(2, n2 & 0xFF); s.port(3, n2 >> 8); s.port(0, 0x01)
        self.wait(lambda: s.rport(0) == 0x01)
        c = 0x01
        for i in range(n2):
            c = (c + 1) & 0x7F or 1
            self.packet(0, data[2*i], data[2*i+1], c, last=(i == n2 - 1))
        self.finish()
    def load_track(self, idx, play=True):
        t = S.track(idx)
        self.cmd(0x0F); self.s.play(int(0.1 * L.SR))
        # free the resident music samples (slots >= 10; 0-9 are the fixed effect samples), then compact
        for sid in range(256):
            slot = self.s.ram(0x4680 + sid) if sid < 0x80 else 0xFF
            if slot != 0xFF and slot >= 10: self.cmd(0x0E, sid)
        self.cmd(0x0E, 0xFF)
        self.cmd(0x25, t['delay'], t['decay'], t['echo'])
        self.status = [(sid, vol, self.sample(sid, vol)) for sid, vol in t['samples']]
        self.upload_seq(t['data'])
        L.LIB.spc_clear_echo(self.s.p)
        return t
    def play(self, seconds, log=True):
        t0 = L.log_start() if log else None
        self.cmd(0x04, 0x7F, 0xD0, 0x0C)
        a = self.s.play(int(seconds * L.SR))
        lg = L.log_take(t0) if log else None
        return a, lg

if __name__ == '__main__':
    import wave
    idx = int(sys.argv[1]); secs = float(sys.argv[2]); out = sys.argv[3]
    d = Driver(); d.load_track(idx)
    a, lg = d.play(secs)
    ev = L.keyons(lg)
    np.save(out.replace('.wav', '_log.npy'), lg)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(L.SR); w.writeframes(a.tobytes())
    print('peak', np.abs(a).max(), 'keyons', len(ev))
    for vc in range(8):
        e = [x for x in ev if x[1] == vc]
        print(vc, len(e), [(round(x[0] / L.SR, 3), hex(x[2]), x[3]) for x in e[:10]])
