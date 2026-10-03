"""Load Surge XT factory patches (.fxp) into the Surge XT VST3 hosted by pedalboard, headlessly.
pedalboard's raw_state for a VST3 is JUCE's "VC2!" + XML <VST3PluginState><IComponent>size.base64</IComponent>; the
IComponent block is Surge's saveRaw() chunk ('sub3' header + patch XML + wavetables), optionally followed by JUCE's
private data. A .fxp file is a 60-byte VST2 program header followed by the same chunk, so we swap the chunk in.
    synth = surge(); load_fxp(synth, path); audio = synth(midi_messages, duration=..., sample_rate=48000)"""
import re, struct
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules; music_paths
from music_paths import MUSIC, DATA  # noqa: E402,F401
from pedalboard import load_plugin

VST3 = os.path.join(MUSIC, 'libs/surge/Surge XT.vst3')
B64 = '.ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+'


def juce_b64_decode(s):
    size_s, data = s.split('.', 1)
    size = int(size_s)
    out = bytearray(size)
    pos = 0
    for ch in data:
        v = B64.index(ch)
        for b in range(6):
            if v & (1 << b):
                byte, bit = divmod(pos + b, 8)
                if byte < size: out[byte] |= (1 << bit)
        pos += 6
    return bytes(out)


def juce_b64_encode(b):
    nbits = len(b) * 8
    chars = []
    for pos in range(0, nbits, 6):
        v = 0
        for k in range(6):
            p = pos + k
            if p < nbits and b[p // 8] & (1 << (p % 8)): v |= (1 << k)
        chars.append(B64[v])
    return f'{len(b)}.' + ''.join(chars)


def surge():
    return load_plugin(VST3)


def get_chunk(plugin):
    st = plugin.raw_state
    m = re.search(rb'<IComponent>([^<]*)</IComponent>', st)
    return juce_b64_decode(m.group(1).decode()), st, m


def load_fxp(plugin, path):
    fxp = open(path, 'rb').read()
    assert fxp[:4] == b'CcnK' and fxp[8:12] == b'FPCh', 'not an opaque-chunk fxp'
    chunk_size = struct.unpack('>i', fxp[56:60])[0]
    patch = fxp[60:60 + chunk_size]
    old, st, m = get_chunk(plugin)
    # keep JUCE private data after Surge's chunk, if present
    k = old.find(b'JUCEPrivateData')
    tail = b''
    if k > 0:
        # JUCE appends: <8-byte magic/size?> 'JUCEPrivateData' ... ; find the start of the private block (a 64-bit size precedes the tag)
        tail = old[k - 8:]
    new = patch + tail
    enc = juce_b64_encode(new).encode()
    xml = st[st.index(b'<?xml'):].split(b'\x00')[0]
    xml2 = xml[:m.start(1) - st.index(b'<?xml')] + enc + xml[m.end(1) - st.index(b'<?xml'):]
    head = st[:st.index(b'<?xml')]
    # VC2! header: 'VC2!' + little-endian uint32 size of the XML (+ terminator)
    newst = b'VC2!' + struct.pack('<I', len(xml2)) + xml2 + b'\x00'     # JUCE copyXmlToBinary: size excludes the NUL
    plugin.raw_state = newst
    plugin([], duration=0.25, sample_rate=48000, num_channels=2, reset=False)   # Surge loads a queued patch on the audio thread
    return plugin


def render(patch_path, notes, total, gain=1.0):
    """notes: (t, dur, midi, vel 0..1) -> (2, n) float32 at 48 kHz"""
    import numpy as np
    from mido import Message
    p = surge(); load_fxp(p, patch_path)
    msgs = []
    for (t, d, n, v) in notes:
        msgs += [Message('note_on', note=int(n), velocity=int(max(1, min(127, v * 127))), time=max(0.0, t)),
                 Message('note_off', note=int(n), velocity=0, time=max(0.0, t) + max(0.02, d))]
    msgs.sort(key=lambda m: m.time)
    y = p(msgs, duration=total, sample_rate=48000, num_channels=2, reset=True)
    return (y * gain).astype(np.float32)
