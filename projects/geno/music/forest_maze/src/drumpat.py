"""Drum patterns as events (t, piece, velocity 0..1) on the 200 BPM clock. Pieces: kick snare hat hatopen ride bell
crash1 crash2 china tom1 tom2 tom3 ftom. One OB = 8 beats = 16 steps (8ths) = 32 half-steps (16ths)."""
import numpy as np

BPM = 200.0; BEAT = 60 / BPM; H = BEAT / 4     # H = our 16th, 0.075 s


def pattern(kind, t0, n_ob, fill=False, crash=True, seed=0, end_crash=False):
    rng = np.random.default_rng(seed)
    ev = []
    nb = n_ob * 8                                   # beats
    def add(t, p, v):
        ev.append((t + rng.normal(0, 0.004), p, float(np.clip(v * (1 + rng.normal(0, 0.09)), 0.05, 1.0))))
    def ghost(t):
        if rng.random() < 0.35: add(t, 'snare', rng.uniform(0.18, 0.32))
    fill_from = nb - 2 if fill else nb + 99         # fill over the last two beats
    for b in range(nb):
        t = t0 + b * BEAT
        in_fill = b >= fill_from
        bar_beat = b % 4
        if kind in ('skank', 'skank8', 'skank16', 'crashride', 'crashride16'):
            if not in_fill:
                if kind == 'skank':
                    if bar_beat in (0, 2): add(t, 'kick', 0.95)
                    if bar_beat in (0, 2) and rng.random() < 0.3: add(t + 2 * H, 'kick', 0.7)
                elif kind == 'crashride16':
                    for q in range(4): add(t + q * H, 'kick', (0.95, 0.7, 0.85, 0.72)[q])
                elif kind in ('skank8', 'crashride'):
                    add(t, 'kick', 0.9); add(t + 2 * H, 'kick', 0.8)
                else:
                    for q in range(4): add(t + q * H, 'kick', (0.92, 0.66, 0.82, 0.7)[q])
                if bar_beat in (1, 3): add(t, 'snare', 0.97 if bar_beat == 3 else 0.9)
                if bar_beat in (0, 2): ghost(t + 3 * H)
                if kind in ('crashride', 'crashride16'):
                    add(t, 'crash1' if b % 2 == 0 else 'crash2', 0.55)
                else:
                    add(t, 'ride', 0.75 if bar_beat % 2 == 0 else 0.6); add(t + 2 * H, 'ride', 0.45)
        elif kind in ('half', 'half16', 'halfride'):
            if not in_fill:
                if bar_beat == 2: add(t, 'snare', 1.0)
                if bar_beat == 1: ghost(t + 3 * H)
                if kind == 'half16':
                    for q in range(4): add(t + q * H, 'kick', (0.92, 0.66, 0.82, 0.7)[q])
                else:
                    if bar_beat == 0: add(t, 'kick', 1.0)
                    if bar_beat == 1: add(t + 2 * H, 'kick', 0.85)
                    if bar_beat == 3: add(t, 'kick', 0.8); add(t + 2 * H, 'kick', 0.7)
                if kind == 'halfride':
                    add(t, 'bell' if bar_beat == 0 else 'ride', 0.7)
                else:
                    add(t, 'china' if bar_beat == 0 and b % 8 == 0 else 'hatopen', 0.6 if bar_beat else 0.75)
        elif kind == 'build':
            # snare 8ths then 16ths, crescendo; kick on beats
            frac = b / max(1, nb - 1)
            sub = 2 if frac < 0.5 else 4
            for q in range(sub):
                add(t + q * (4 // sub) * H, 'snare', 0.35 + 0.6 * frac)
            add(t, 'kick', 0.9)
        elif kind == 'trem':
            # transition: double-kick 16ths with snare on 2/4 and hats 8ths
            for q in range(4): add(t + q * H, 'kick', 0.8 if q % 2 == 0 else 0.66)
            if bar_beat in (1, 3): add(t, 'snare', 0.9)
            add(t, 'hat', 0.6); add(t + 2 * H, 'hat', 0.45)
        elif kind == 'electro':
            # four on the floor (every beat), snare + clap on 2 and 4, open hat on the offbeat 8th, 16th closed hats
            if not in_fill:
                add(t, 'kick', 0.95); add(t, 'kick808', 1.0)
                if bar_beat in (1, 3): add(t, 'snare', 0.8); add(t, 'clap', 0.9)
                add(t + 2 * H, 'hatopen', 0.55)
                for q in (1, 3): add(t + q * H, 'hat', 0.3)
        elif kind == 'none':
            pass
        if in_fill:
            toms = ['tom1', 'tom1', 'tom2', 'tom2', 'tom3', 'tom3', 'ftom', 'ftom']
            k = (b - fill_from) * 4
            for q in range(4):
                p = 'snare' if (k + q) < 2 else toms[min(7, k + q)]
                add(t + q * H, p, 0.7 + 0.04 * (k + q))
                if q % 2 == 0: add(t + q * H, 'kick', 0.8)
    ev = [(t, pc, min(1.0, v * 1.1)) if (pc in ('kick', 'snare') and abs(((t - t0) / BEAT) % 4) < 0.05) else (t, pc, v) for (t, pc, v) in ev]
    if crash:
        add(t0, 'crash1', 1.0); add(t0, 'kick', 1.0)
    if end_crash:
        add(t0 + nb * BEAT, 'crash2', 1.0)
    return ev


def hits(times, t0=0.0, china=False):
    ev = []
    for t in times:
        ev += [(t0 + t, 'kick', 1.0), (t0 + t, 'crash1', 1.0), (t0 + t, 'snare', 0.9)]
        if china: ev.append((t0 + t, 'china', 0.9))
    return ev
