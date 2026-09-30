"""Chart sunmeasure.py's frame-by-frame radii: Geno Flash's sun before and after, one panel each on one radius axis
(units), the hitbox dashed grey in both; the body's edge (glow median), the corona's median reach, and the faintest
trace; a line for the cast's big-blast margin (PK Flash's median edge over its hitbox).
    .venv/bin/python projects/geno/fx/sunchart.py OUT.png BEFORE.json AFTER.json [--disc DISC.json] [--bdisc DISC.json]
        [--pk PK.json] [--csv OUT.csv] [--titles 'BEFORE|AFTER'] [--xmax N]
BEFORE/AFTER hold one drawn run each (sunmeasure's LABEL); a disc-only run's json gives the after panel its disc edge.
"""
import json, sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

SURF, INK, INK2, GRID, HIT = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df', '#8a8984'
S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'          # the reference palette's first three slots, in order


def sun_rows(path):
    d = json.load(open(path))
    rows, peak = [], 0
    for r in d['rows']:
        if r['hit'] < 3 or r['hit'] < peak - 2:        # the red flash's particles after the sun (not a hitbox)
            continue
        peak = max(peak, r['hit'])
        rows.append(r)
    return rows


def series(rows, label, key):
    """One drawn measure's median edge per frame, from the model's first drawn frame (it draws the frame after the
    hitbox appears)."""
    xs, ys = [], []
    for r in rows:
        e = r.get(label + key)
        if e and e['med'] > 0.5 * r['hit']:
            xs.append(r['rel']); ys.append(e['med'])
    return np.array(xs), np.array(ys)


def end_labels(ax, items, gap=2.6):
    """Direct labels at the lines' right ends, nudged apart so none overlap."""
    items = sorted(items, key=lambda t: t[1])
    ys = [t[1] for t in items]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + gap)
    for (x, _, name), y in zip(items, ys):
        ax.annotate(name, (x, y), xytext=(6, 0), textcoords='offset points', va='center', fontsize=8.5, color=INK2)


def write_csv(path, bp, ap, disc, bdisc=None):
    """Every frame of the sun, before and after: the hitbox's radius (units), and each drawn measure's median edge as a
    multiple of it (the disc, from a disc-only run, when given)."""
    import csv
    def by_rel(p):
        if not p:
            return {}, None
        rows = sun_rows(p)
        lab = [k for k in rows[1] if k not in ('rel', 'hit') and not k.endswith(('_faint', '_core'))][0]
        x0 = rows[0]['rel']
        return {r['rel'] - x0: r for r in rows}, lab
    f = lambda r, k: f"{r[k]['med'] / r['hit']:.2f}" if r and k and k in r and r[k]['med'] > 0.5 * r['hit'] else ''
    sides = []
    for name, main_p, disc_p in (('before', bp, bdisc), ('after', ap, disc)):
        (m, ml), (d, dl) = by_rel(main_p), by_rel(disc_p)
        sides.append((name, m, ml, d, dl))
    frames = sorted(set().union(*[set(m) for _, m, _, _, _ in sides]))
    with open(path, 'w', newline='') as fh:
        w = csv.writer(fh)
        head = ['frame']
        for name, m, ml, d, dl in sides:
            head += [f'{name}: hitbox r'] + ([f'{name}: disc x'] if dl else []) + [f'{name}: drawn edge x', f'{name}: faintest x']
        w.writerow(head)
        for fr in frames:
            row = [fr]
            for name, m, ml, d, dl in sides:
                r = m.get(fr)
                row += [f"{r['hit']:.1f}" if r else ''] + ([f(d.get(fr), dl)] if dl else []) + [f(r, ml), f(r, ml + '_faint' if ml else None)]
            w.writerow(row)


def main():
    a = sys.argv[1:]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    out, bp, ap = a[0], a[1], a[2]
    disc = opt('--disc')
    pk = opt('--pk')
    pk_ratio = None
    if pk:
        pr = [r for r in json.load(open(pk))['rows'] if r['hit'] > 3]
        lab = [k for k in pr[0] if k not in ('rel', 'hit') and not k.endswith(('_faint', '_core'))][0]
        pk_ratio = float(np.median([r[lab]['med'] / r['hit'] for r in pr if lab in r]))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True, facecolor=SURF)
    titles = (opt('--titles') or 'Before: the star rounding into the smiling sun, with a halo|After: one sun, a disc with a corona').split('|')
    bdisc = opt('--bdisc')
    for ax, path, title, extra in ((axes[0], bp, titles[0], bdisc), (axes[1], ap, titles[1], disc)):
        rows = sun_rows(path)
        lab = [k for k in rows[1] if k not in ('rel', 'hit') and not k.endswith(('_faint', '_core'))][0]
        x = np.array([r['rel'] for r in rows]); h = np.array([r['hit'] for r in rows])
        x0 = x[0]
        ax.set_facecolor(SURF)
        ax.plot(x - x0, h, color=HIT, lw=2, ls=(0, (4, 3)), label='hitbox radius')
        lines = []
        if extra:
            dr = sun_rows(extra)
            dl = [k for k in dr[1] if k not in ('rel', 'hit') and not k.endswith(('_faint', '_core'))][0]
            dx, dy = series(dr, dl, '')
            lines.append((dx - x0, dy, S1, 'disc edge'))
            gx, gy = series(rows, lab, '')
            lines.append((gx - x0, gy, S2, 'corona (median edge)'))
        else:
            gx, gy = series(rows, lab, '')
            lines.append((gx - x0, gy, S1, 'drawn edge (disc)'))
        fx, fy = series(rows, lab, '_faint')
        lines.append((fx - x0, fy, S3, 'faintest trace'))
        labels = [(x[-1] - x0, h[-1], 'hitbox')]
        for lx, ly, col, name in lines:
            ax.plot(lx, ly, color=col, lw=2, label=name)
            labels.append((lx[-1], ly[-1], name))
        if pk_ratio:
            ax.plot(x - x0, h * pk_ratio, color='#c9c8c3', lw=1.2, zorder=0)
            labels.append((x[-1] - x0, h[-1] * pk_ratio, f"PK Flash's median ({pk_ratio:.2f}x)"))
        end_labels(ax, labels)
        ax.set_title(title, fontsize=10.5, color=INK, loc='left')
        ax.set_xlabel('frames from the sun\'s first frame (growth 0-40, linger to 70)', fontsize=9, color=INK2)
        ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(colors=INK2, labelsize=8.5)
        ax.set_xlim(-2, float(opt('--xmax') or 100))
        ax.legend(loc='lower right', fontsize=8, frameon=False, labelcolor=INK2)
    axes[0].set_ylabel('radius (units)', fontsize=9, color=INK2)
    fig.suptitle("Geno Flash's sun against its hitbox, every frame (flash_scale_lab, fx/sunmeasure.py)", fontsize=11.5,
                 color=INK, x=0.01, ha='left')
    fig.tight_layout()
    fig.savefig(out, dpi=130, facecolor=SURF)
    csv_out = opt('--csv')
    if csv_out:
        write_csv(csv_out, bp, ap, disc, bdisc)
    print('wrote', out, 'pk', pk_ratio)


if __name__ == '__main__':
    main()
