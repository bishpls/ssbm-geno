"""Render an SPC state in blargg's snes_spc (local copy with a DSP write log) and extract per-voice key-on events."""
import ctypes, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'sound', 'capture'))   # spcharness, paths
LIB = ctypes.CDLL(os.path.expanduser(os.environ.get('SPCLOG_LIB', '~/games/melee/work/music/fanfare/tools/spclog/libspclog.dylib')))   # ../spclog
LIB.spc_new.restype = ctypes.c_void_p
for fn, args in [('spc_load_spc', [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long]),
                 ('spc_write_port', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]),
                 ('spc_read_port', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]),
                 ('spc_play', [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_short)]),
                 ('spc_delete', [ctypes.c_void_p]), ('spc_clear_echo', [ctypes.c_void_p]),
                 ('spcx_dsp_write', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]),
                 ('spcx_dsp_read', [ctypes.c_void_p, ctypes.c_int]),
                 ('spcx_ram_read', [ctypes.c_void_p, ctypes.c_int]),
                 ('spcx_ram_write', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]),
                 ('spcx_log_enable', [ctypes.c_int]), ('spcx_log_clear', []), ('spcx_log_count', []),
                 ('spcx_log_data', []), ('spcx_samples', [])]:
    getattr(LIB, fn).argtypes = args
LIB.spc_load_spc.restype = ctypes.c_char_p
LIB.spc_play.restype = ctypes.c_char_p
LIB.spcx_log_count.restype = ctypes.c_long
LIB.spcx_samples.restype = ctypes.c_long
LIB.spcx_log_data.restype = ctypes.POINTER(ctypes.c_int)
SR = 32000

class Spc:
    def __init__(self, data):
        self.p = LIB.spc_new(); err = LIB.spc_load_spc(self.p, data, len(data)); assert err is None, err
    def play(self, n):
        buf = (ctypes.c_short * (2 * n))(); err = LIB.spc_play(self.p, 2 * n, buf); assert err is None, err
        return np.frombuffer(buf, dtype=np.int16).reshape(-1, 2).copy()
    def ram(self, a): return LIB.spcx_ram_read(self.p, a)
    def wram(self, a, v): LIB.spcx_ram_write(self.p, a, v)
    def port(self, i, v): LIB.spc_write_port(self.p, 0, i, v)
    def rport(self, i): return LIB.spc_read_port(self.p, 0, i)
    def dsp(self, a, v=None):
        if v is None: return LIB.spcx_dsp_read(self.p, a)
        LIB.spcx_dsp_write(self.p, a, v)

def log_start():
    LIB.spcx_log_clear(); LIB.spcx_log_enable(1); return LIB.spcx_samples()

def log_take(t0):
    n = LIB.spcx_log_count(); d = LIB.spcx_log_data()
    a = np.ctypeslib.as_array(d, shape=(3 * n,)).reshape(-1, 3).copy()
    LIB.spcx_log_enable(0); LIB.spcx_log_clear()
    a[:, 0] -= t0
    a[:, 2] &= 0xFF   # the SPC core passes extra bits above the data byte
    return a

def keyons(log):
    """-> list of (sample, voice, pitch_reg, srcn, vol_l, vol_r) using the register shadow at KON time."""
    regs = np.zeros(128, int); ev = []
    for t, a, v in log:
        if a == 0x4C and v:
            for vc in range(8):
                if v >> vc & 1:
                    b = vc << 4
                    ev.append((int(t), vc, regs[b+2] | (regs[b+3] << 8), int(regs[b+4]), int(regs[b]), int(regs[b+1])))
        regs[a] = v
    return ev

def keyons_settled(log, settle=96):
    """Like keyons(), but P/SRCN/VOL are read `settle` samples after the KON write (the driver writes pitch after KON)."""
    regs = np.zeros(128, int); pend = []; ev = []
    for t, a, v in log:
        while pend and t >= pend[0][0] + settle:
            t0, vc = pend.pop(0); b = vc << 4
            ev.append((int(t0), vc, regs[b+2] | (regs[b+3] << 8), int(regs[b+4]), int(regs[b]), int(regs[b+1])))
        regs[a] = v
        if a == 0x4C and v:
            for vc in range(8):
                if v >> vc & 1: pend.append((int(t), vc))
    return sorted(ev)
