"""Independent ear: basic-pitch transcribes a render; recall of each lead line's notes (pitch within a semitone-exact
match, onset within 60 ms; octave-agnostic count too) and of the harmony, per section."""
import sys, os, subprocess, csv, tempfile, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import levelup as LU
BP = os.environ.get('BASIC_PITCH', 'basic-pitch')   # Spotify's basic-pitch CLI (its own Python 3.11 venv here)

def transcribe(wav):
    d = tempfile.mkdtemp()
    subprocess.run([BP, d, wav, '--save-note-events'], check=True, capture_output=True)
    f = [x for x in os.listdir(d) if x.endswith('.csv')][0]
    rows = list(csv.reader(open(os.path.join(d, f))))[1:]
    return [(float(r[0]), float(r[1]), int(r[2]), float(r[3])) for r in rows]

def recall(det, ref, tol=0.06):
    hit = hit_pc = 0
    for (t, d, p) in ref:
        cand = [q for (s, e, q, a) in det if abs(s - t) <= tol]
        hit += any(q == p for q in cand); hit_pc += any(q % 12 == p % 12 for q in cand)
    return round(hit / len(ref), 2), round(hit_pc / len(ref), 2)

if __name__ == '__main__':
    T = LU.T16
    def line(bar, items, octave=0):
        return [((bar * 16 + pos) * T, ln * T, LU.m(nm) + 12 * octave) for (pos, nm, ln) in items]
    lines = {'intro run': line(0, LU.RUN0), 'intro thirds (upper)': line(0, LU.THIRD_HI),
             'theme melody (tpt, 8va)': line(1, LU.MEL[1], 1) + line(2, LU.MEL[2], 1),
             'theme melody (horns, orig. register)': line(1, LU.MEL[1]) + line(2, LU.MEL[2]),
             'theme harmony (tpt 2, 8va)': line(1, LU.HAR[1], 1) + line(2, LU.HAR[2], 1),
             'bass': line(1, LU.BASS[1]) + line(2, LU.BASS[2]) + line(3, LU.BASS[3]),
             'V-bar run': line(3, LU.RUN1)}
    for wav in sys.argv[1:]:
        det = transcribe(wav)
        print(wav.split('/')[-2], len(det), 'notes detected')
        for k, v in lines.items():
            print('   %-38s exact %.2f  pitch-class %.2f' % ((k,) + recall(det, v)))
