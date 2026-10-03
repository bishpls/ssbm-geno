"""Decode the announcer recordings the "Geno!" splice cuts from, out of your own disc's banks, into src/ (12 kHz mono WAVs
named as splice.py loads them). Nothing here is shipped: src/ is game audio and stays local.
    python tools/sources.py [DISC_ROOT]      # default $MELEE_DISC or ~/games/melee/disc
Reads files/audio/us/nr_name.ssm (the US name calls) and files/audio/us/nr_vs.ssm ("No contest!", "Green team!"). The
name bank may already be patched with Geno's call: only entry 17 changes, and no source below reads it."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import ssm

HERE = os.path.expanduser(os.environ.get('ANNOUNCER_WORK', os.path.join(os.environ.get('MELEE_WORK', '~/games/melee/work'), 'announcer')))   # the work folder (game audio)
# src name -> (bank, entry index): the clips segments are cut from (NOTES.md §3 and §7)
SOURCES = {
    'defeated': ('nr_name', 34), 'falco': ('nr_name', 4), 'ganondorf': ('nr_name', 6), 'giant': ('nr_name', 7),
    'gigabowser': ('nr_name', 8), 'go': ('nr_name', 38), 'jigglypuff': ('nr_name', 13), 'kirby': ('nr_name', 15),
    'mario': ('nr_name', 21), 'ness': ('nr_name', 26), 'peach': ('nr_name', 27), 'pichu': ('nr_name', 28),
    'sheik': ('nr_name', 32), 'team': ('nr_name', 49), 'three_a': ('nr_name', 37), 'three_b': ('nr_name', 46),
    'yoshi': ('nr_name', 31), 'zelda': ('nr_name', 33),
    'nocontest': ('nr_vs', 0), 'greenteam': ('nr_vs', 3),
}


def main():
    disc = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('MELEE_DISC', '~/games/melee/disc'))
    banks = {b: ssm.parse(os.path.join(disc, 'files', 'audio', 'us', b + '.ssm')) for b in ('nr_name', 'nr_vs')}
    out = os.path.join(HERE, 'src'); os.makedirs(out, exist_ok=True)
    for name, (b, i) in SOURCES.items():
        s = banks[b]['sounds'][i]
        assert s['nch'] == 1 and s['rate'] == 12000, (name, s['nch'], s['rate'])
        x = ssm.decode_channel(banks[b], s['chans'][0])
        ssm.write_wav(os.path.join(out, name + '.wav'), x, s['rate'])
    print(f'{len(SOURCES)} source clips -> {out}')


if __name__ == '__main__':
    main()
