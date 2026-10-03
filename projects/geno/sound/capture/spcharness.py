"""Drive SMRPG's SPC700 sound driver in blargg's snes_spc (accurate DSP) and render sound effects.

State: an ARAM/DSP/register dump taken by Mesen2 during a battle (driver + battle SFX set + fixed samples loaded).
Protocol (from the driver's code at $0308 / $04B6):
  play SFX:  port3 = token<<4 | priority, port1 = sfx id, port2 = $80 (pan/param), then port0 = $08 (voices 6+7)
             or $09 (voices 4+5). The driver echoes the token on port1 and clears ports 0/1 via $F1.
  other commands ($01-$33): write port0 = cmd, wait for $FF on port0, write port0 = 0.
"""
import ctypes, struct, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
LIB = ctypes.CDLL(paths.SPCLIB)
LIB.spc_new.restype = ctypes.c_void_p
for fn, args in [('spc_load_spc', [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long]),
                 ('spc_write_port', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]),
                 ('spc_read_port', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]),
                 ('spc_play', [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_short)]),
                 ('spc_clear_echo', [ctypes.c_void_p]), ('spc_delete', [ctypes.c_void_p]),
                 ('spc_mute_voices', [ctypes.c_void_p, ctypes.c_int]),
                 ('spcx_dsp_write', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]),
                 ('spcx_dsp_read', [ctypes.c_void_p, ctypes.c_int]),
                 ('spcx_ram_read', [ctypes.c_void_p, ctypes.c_int]),
                 ('spcx_ram_write', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]),
                 ('spcx_pc', [ctypes.c_void_p]), ('spcx_set_dry', [ctypes.c_void_p, ctypes.c_int]), ('spcx_set_nosat', [ctypes.c_int])]:
    getattr(LIB, fn).argtypes = args
LIB.spc_load_spc.restype = ctypes.c_char_p
LIB.spc_play.restype = ctypes.c_char_p
SR = 32000

def build_spc(prefix):
    """SPC file bytes from a Mesen2 dump (prefix.aram / .dsp / .state.txt)."""
    ram = bytearray(open(prefix + '.aram', 'rb').read())
    dsp = open(prefix + '.dsp', 'rb').read()
    st = {}
    for line in open(prefix + '.state.txt'):
        k, v = line.strip().split('=', 1); st[k] = v
    g = lambda k: int(st[k]) if st[k] not in ('true', 'false') else int(st[k] == 'true')
    ctrl = sum((g('spc.timer%d.enabled' % i) << i) for i in range(3)) | (0x80 if g('spc.romEnabled') else 0)
    ram[0xF1] = ctrl
    ram[0xF2] = g('spc.dspReg')
    for i in range(4): ram[0xF4 + i] = g('spc.cpuRegs[%d]' % i)
    ram[0xF8] = g('spc.ramReg[0]'); ram[0xF9] = g('spc.ramReg[1]')
    for i in range(3): ram[0xFA + i] = g('spc.timer%d.target' % i) & 0xFF
    for i in range(3): ram[0xFD + i] = g('spc.timer%d.output' % i) & 0x0F
    hdr = bytearray(0x100)
    hdr[0:33] = b'SNES-SPC700 Sound File Data v0.30'; hdr[33] = 26; hdr[34] = 26; hdr[35] = 27; hdr[36] = 30
    pc = g('spc.pc'); hdr[0x25] = pc & 0xFF; hdr[0x26] = pc >> 8
    hdr[0x27] = g('spc.a'); hdr[0x28] = g('spc.x'); hdr[0x29] = g('spc.y'); hdr[0x2A] = g('spc.ps'); hdr[0x2B] = g('spc.sp')
    return bytes(hdr) + bytes(ram) + dsp + bytes(0x40) + bytes(ram[0xFFC0:0x10000])

class Spc:
    def __init__(self, spcdata):
        self.p = LIB.spc_new()
        self.data = spcdata
        self.reload()
    def reload(self):
        err = LIB.spc_load_spc(self.p, self.data, len(self.data))
        assert err is None, err
        self.out = []
    def play(self, seconds=None, samples=None):
        n = samples if samples is not None else int(round(seconds * SR))
        buf = (ctypes.c_short * (2 * n))()
        err = LIB.spc_play(self.p, 2 * n, buf); assert err is None, err
        a = np.frombuffer(buf, dtype=np.int16).reshape(-1, 2).copy()
        self.out.append(a); return a
    def dry(self, on=True): LIB.spcx_set_dry(self.p, int(on))
    def port(self, i, v): LIB.spc_write_port(self.p, 0, i, v)
    def rport(self, i): return LIB.spc_read_port(self.p, 0, i)
    def dsp(self, a, v=None):
        if v is None: return LIB.spcx_dsp_read(self.p, a)
        LIB.spcx_dsp_write(self.p, a, v)
    def ram(self, a): return LIB.spcx_ram_read(self.p, a)
    def wait(self, cond, maxs=0.2, step=32):
        t = 0
        while not cond() and t < maxs * SR:
            self.play(samples=step); t += step
        return cond()
    def command(self, cmd, p1=0, p2=0, p3=0):
        """Generic command with $FF handshake."""
        self.port(1, p1); self.port(2, p2); self.port(3, p3); self.port(0, cmd)
        ok = self.wait(lambda: self.rport(0) == 0xFF)
        self.port(0, 0)
        self.wait(lambda: self.rport(0) == 0x00)
        return ok
    def sfx(self, sid, cmd=0x08, pan=0x80, prio=0x0F, token=None):
        if token is None: token = (self.rport(1) + 1) & 0x0F or 1
        self.port(3, (token << 4) | prio); self.port(1, sid); self.port(2, pan); self.port(0, cmd)
        ok = self.wait(lambda: self.rport(1) == token)
        self.port(0, 0)
        return ok
    def take(self):
        a = np.concatenate(self.out) if self.out else np.zeros((0, 2), np.int16)
        self.out = []; return a

def write_wav(path, a, sr=SR):
    import wave
    a = np.asarray(a, dtype=np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(a.shape[1] if a.ndim > 1 else 1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(a.tobytes())

FRAME = 1.0 / 60.0988   # NTSC frame, for script waits

def render_sequence(spcdata, events, dry=True, tail=0.6, maxs=12.0, stop_first=True, nosat=False):
    """events: list of (time_s, sfx_id, cmd) with cmd 0x08 (script channel 6 -> voices 6/7) or 0x09 (channel 4 -> voices 4/5).
    Sends each command at its sample time, keeps rendering until everything is silent for `tail` s. Returns int16 stereo."""
    LIB.spcx_set_nosat(int(nosat))
    s = Spc(spcdata)
    if dry: s.dry(True)
    s.play(0.25)
    if stop_first:
        s.command(0x0F); s.play(0.3); LIB.spc_clear_echo(s.p); s.play(0.1); LIB.spc_clear_echo(s.p); s.play(0.1)
    s.take()
    ev = sorted(events)
    t = 0; blk = 64; quiet = 0; started = False; k = 0
    while t < maxs * SR:
        while k < len(ev) and ev[k][0] * SR <= t:
            _, sid, cmd = ev[k]; s.sfx(sid, cmd=cmd); k += 1
        a = s.play(samples=blk); t += blk
        loud = np.abs(a.astype(int)).max() > 2
        if loud: started = True; quiet = 0
        else: quiet += blk
        if k >= len(ev) and started and quiet > tail * SR: break
    a = s.take()
    LIB.spc_delete(s.p)
    LIB.spcx_set_nosat(0)
    return a
