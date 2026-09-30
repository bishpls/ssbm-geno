"""Report a Kirby-copy lab run (kirby_lab, kirby_trio_lab, kirby_cpu_lab): per segment, the copies gained and lost, the
copy's shots, and each neutral B from the press to the shot, for Kirby's copy (states 544-551) and for Geno himself
(343-358), so the two frame counts can be compared line by line.
    .venv/bin/python projects/geno/director/labs/report_kirby.py RUN/osreport.log [projects/geno/director/build/LAB.json]
"""
import json, sys

KB_GE = set(range(544, 552))     # ftKb_MS_GeSpecialNStart .. GeSpecialAirNFinger
GE_N = {343, 344, 345, 346, 347, 348, 357, 358}   # Geno's neutral B states
NAMES = {544: 'start', 545: 'loop', 546: 'end', 547: 'air start', 548: 'air loop', 549: 'air end', 550: 'finger',
         551: 'air finger', 343: 'start', 344: 'loop', 345: 'end', 346: 'air start', 347: 'air loop', 348: 'air end',
         357: 'finger', 358: 'air finger'}


def main(log, labels_json=None):
    meta = json.load(open(labels_json)) if labels_json else {}
    labels = dict(meta.get('labels', []))
    chars = meta.get('chars', [])          # state numbers are per kind: 544-551 are Kirby's, 343-358 Geno's
    mine = lambda port: {'kirby': KB_GE, 'geno': GE_N}.get(chars[port] if port < len(chars) else '', KB_GE | GE_N)
    marks, events, press, last = {}, [], {}, {}
    for line in open(log, errors='replace'):
        w = line.split()
        if not w:
            continue
        if w[0] == 'MARK':
            marks[int(w[1])] = labels.get(int(w[1]), w[2]); events.append((int(w[1]), f'== {marks[int(w[1])]}'))
        elif w[0] == 'MS':
            s, port, ms = int(w[1]), int(w[2]), int(w[3])
            nb = ms in mine(port)
            if nb and last.get(port) not in mine(port):
                press[port] = s              # a neutral B begins (a start, or a stored charge's release)
            last[port] = ms
            if nb:
                who = 'kirby' if ms in KB_GE else 'geno'
                events.append((s, f'   {s:6d} p{port} {who:5s} {NAMES[ms]:10s} ({ms})'))
        elif w[0] == 'LASER':
            s, port = int(w[1]), int(w[2])
            since = f'  {s - press[port]} frames from the press' if port in press else ''
            events.append((s, f'   {s:6d} p{port} shot{since}'))
        elif w[0] in ('KBCOPY', 'KBLOSE'):
            events.append((None, '   ' + line.strip()))
        elif w[0] in ('KBGE',) and w[1] in ('STORE', 'STAR'):
            events.append((None, '   ' + line.strip()))
    for _, e in events:
        print(e)


if __name__ == '__main__':
    main(*sys.argv[1:3])
