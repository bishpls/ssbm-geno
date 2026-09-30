"""showcase_manifest.py TAG OUT.json: the showcase reel's manifest from the TAG_* captures (showcase_capture.sh), in the
reel's order: the title, the entrance, the moveset (showcase_lab parts a-c), the results screens, the costumes, Kirby's
hat, the end card. RES: the results screens' timing and crops, and the Kirby clips."""
import json, os, sys
S = os.path.expanduser('~/games/melee/sandbox/geno-atk-air/runs')
tag, out = sys.argv[1], sys.argv[2]
R = lambda name: f'../runs/{tag}_{name}'
segs = lambda part: [x['label'] for x in json.load(open(f'{S}/{tag}_part_{part}.plan.json'))]
man = [{"card": "title", "frames": 150}, {"run": R('entry'), "seg": "entry"}]
for part in 'abc':
    for lab in segs(part):
        man.append({"run": R(f'part_{part}'), "seg": lab})
RES = {"win_B": {"from": 0.0, "frames": 86, "box": [0, 0, 1, 1], "gain": 0.5}, "win_Y": {"from": 0.0, "frames": 120, "box": [0, 0, 1, 1], "gain": 0.5}, "win_X": {"from": 0.0, "frames": 82, "box": [0, 0, 1, 1], "gain": 0.5}, "lose": {"from": 0.0, "frames": 110, "box": [0, 0, 1, 1], "gain": 0.4, "inset": [0.09, 0.66, 0.24, 0.9]}, "kirby": [{"seg": "copy_c0", "from": 2, "to": 112, "caption": "Kirby's Geno hat"}, {"seg": "charge", "from": 2, "to": 104, "caption": "Kirby's copy: the Geno Beam"}]}
for key, cap in (('win_B', 'Victory pose 1'), ('win_Y', 'Victory pose 2'), ('win_X', 'Victory pose 3'), ('lose', 'Losing: the clap')):
    r = RES.get(key, {})
    man.append(dict({"run": R(key), "results": cap, "from": 0.0, "frames": 150, "box": [0, 0, 1, 1], "gain": 0.5}, **r))
man.append({"lineup": [R('costumes_012'), R('costumes_345')], "frames": 150, "caption": "Costumes"})
K = RES.get('kirby', [])
for k in K:
    man.append(dict(k, run=R('kirby')))
man.append({"card": "end", "frames": 150})
json.dump(man, open(out, 'w'), indent=1)
print(len(man), 'entries ->', out)
