"""The shortlist for Michael: each chosen candidate alone, after a real chant, and looped as the game plays it, a spectrogram
board against real chants, the ranking table (from cands/eval.json), and the review page (local; it links local files and
is never published). Everything written goes to $CROWD_WORK.

    .venv/bin/python projects/geno/sound/cheer/deliver.py NAME [NAME ...] [--ingame RUN_PLATES_DIR ...]
The names are ranked in the order given. --ingame takes mp4s made from the cheer lab's captures (see cheer_lab.py).
"""
import argparse, json, os, shutil, subprocess, sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crowdsplice as cs  # noqa: E402
from evaluate import CONTEXT, GAP  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
OUT = os.path.join(cs.WORK, 'shortlist')
REFS = [('Kb', 'Kirby: "Kir-by! Kir-by!" (two syllables, two cycles; the rhythm template)'),
        ('Pc', 'Pichu: "Pi-chu!" (the "EE" and the "ch")'), ('Pe', 'Peach: "Go Peach!" (the "o" of "Go")'),
        ('Fc', 'Falco: "Fal-co!" (the "o" and its decay)'), ('Mr', 'Mario: "Ma-ri-o!"'),
        ('Lg', 'Luigi: "Lu-i-gi!" (a real "gee")'), ('Pr', 'Jigglypuff: "Jig-gly-puff!" (the chant-initial "J")'),
        ('Ns', 'Ness: "Ness! Ness! Ness!" (the "n")')]


def spec_board(paths, labels, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import librosa
    fig, axs = plt.subplots(len(paths), 1, figsize=(12, 1.7 * len(paths)))
    for ax, p, l in zip(np.atleast_1d(axs), paths, labels):
        x, sr = sf.read(p)
        S = librosa.amplitude_to_db(np.abs(librosa.stft(x, n_fft=512, hop_length=64)), ref=np.max)
        ax.imshow(S, origin='lower', aspect='auto', extent=[0, len(x) / sr, 0, sr / 2000], vmin=-60, cmap='magma')
        ax.set_xlim(0, 2.8); ax.set_ylabel('kHz', fontsize=7); ax.tick_params(labelsize=7)
        ax.set_title(l, fontsize=8, loc='left')
    plt.tight_layout(); plt.savefig(out, dpi=80); plt.close(fig)


def row(ev, name):
    e = ev.get(name, {})
    w = e.get('whisper', {})
    cells = []
    for m in ('small.en', 'medium.en', 'turbo'):             # (turbo's cast choice favours short names; not shown)
        v = w.get(m)
        cells.append(f"{m}: alone '{v['free_alone'][:40]}', in context '{v['free_ctx'][:60]}', "
                     f"P(Geno) {v['p_hit_alone']:.2f} / {v['p_hit_ctx']:.2f}" if v else f'{m}: -')
    ph = e.get('phones')
    if ph:
        cells.append('phones ' + ' '.join(f"{k} {ph[k][0][0]} {ph[k][0][1]:.2f}" for k in ('onset', 'vowel', 'nasal', 'final')))
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='+')
    ap.add_argument('--ingame', nargs='*', default=[], help='CAPTION::path.mp4')
    ap.add_argument('--recipe', default='{}', help='JSON {name: one-line recipe}')
    ap.add_argument('--more', nargs='*', default=[], help="more page items at the end: '#Heading' or 'path::caption'")
    a = ap.parse_args()
    meta = json.load(open(os.path.join(cs.WORK, 'cands', 'cands.json')))
    ev = json.load(open(os.path.join(cs.WORK, 'cands', 'eval.json')))
    recipes = json.loads(a.recipe)
    os.makedirs(OUT, exist_ok=True)
    ctx = cs.load(CONTEXT)
    rank, items = [], []
    for i, n in enumerate(a.names, 1):
        y, _ = sf.read(meta[n]['path'])
        base = os.path.join(OUT, f'{i}_{n}')
        cs.write(base + '.wav', y)
        cs.write(base + '_after_kirby.wav', np.concatenate([ctx, np.zeros(int(GAP * cs.SR)), y]))
        cs.write(base + '_loop3.wav', np.concatenate([y, y, y]))
        rank.append(dict(rank=i, name=n, wav=base + '.wav', recipe=recipes.get(n, ''), sec=meta[n]['sec'], lufs=meta[n]['lufs'],
                         peak_dbfs=meta[n]['peak_dbfs'], segs=meta[n]['segs'], eval=ev.get(n)))
    board = os.path.join(OUT, 'spectrograms.png')
    spec_board([r['wav'] for r in rank] + [os.path.join(cs.WORK, 'chants', f) for f in
                                           sorted(os.listdir(os.path.join(cs.WORK, 'chants'))) if f.startswith('us_Kb_')],
               [f"{r['rank']}. {r['name']}" for r in rank] + ['real: Kirby "Kir-by! Kir-by!"'], board)
    json.dump(rank, open(os.path.join(OUT, 'ranking.json'), 'w'), indent=1, ensure_ascii=False)

    # ---- the page
    items = ['#The candidates (ranked; each alone, then after the crowd\'s real "Kir-by! Kir-by!", then looped x3 as the game replays it)']
    for r in rank:
        b = r['wav'][:-4]
        cap = f"{r['rank']}. {r['name']} ({r['sec']:.2f} s, {r['lufs']:.1f} LUFS). {r['recipe']}"
        items += [f"{r['wav']}::{cap}", f"{b}_after_kirby.wav::{r['rank']}. after the real Kirby chant: "
                  + ' | '.join(row(ev, r['name'])), f"{b}_loop3.wav::{r['rank']}. looped x3 (in a match the crowd plays it 8 times)"]
    items.append(f'{board}::Spectrograms: the candidates and a real two-syllable chant (Kirby).')
    if a.ingame:
        items.append('#In game (the cheer lab: Geno at 120% forward-smashes two Foxes; Dolphin frames with the game\'s own audio)')
        for g in a.ingame:
            cap, p = g.split('::', 1)
            items.append(f'{p}::{cap}')
    items.append('#The real chants the pieces come from')
    for code, cap in REFS:
        p = [f for f in os.listdir(os.path.join(cs.WORK, 'chants')) if f.startswith(f'us_{code}_')][0]
        items.append(f"{os.path.join(cs.WORK, 'chants', p)}::{cap}")
    for m in a.more:
        items.append(m if m.startswith('#') else m)
    page = os.path.join(OUT, 'review_cheer.html')
    note = ('"Ge-no! Ge-no!" (JEE-no) for the crowd, spliced only from the crowd\'s own recorded chants on the disc: cuts, '
            'time-scaling (WSOLA), small pitch moves (varispeed), gains and crossfades. No TTS, cloning or voice conversion; '
            'Whisper and wav2vec2 ran locally, only to rank. All files are 16 kHz like the retail chants, peak -3 dBFS.')
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'machinima', 'melee', 'art', 'review_page.py'), page,
                    'Crowd cheer: "Ge-no! Ge-no!"', '--sound', '--note', note] + items, check=True)
    print(page)


if __name__ == '__main__':
    main()
