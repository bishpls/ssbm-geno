"""Minimal Neural Amp Modeler (NAM) WaveNet runtime in PyTorch: loads a .nam capture (standard WaveNet, v0.5 export)
and processes mono float audio at 48 kHz.   y = NAM('amps/x.nam')(x)
Weight order follows NAM's export: per layer array [rechannel, per layer (conv w, conv b, input_mixer w, 1x1 w, 1x1 b),
head_rechannel w (+b)], then head_scale."""
import json, numpy as np, torch
import torch.nn.functional as F


class NAM:
    def __init__(self, path):
        j = json.load(open(path))
        assert j['architecture'] == 'WaveNet', j['architecture']
        self.cfg = j['config']; self.sr = j.get('sample_rate') or 48000
        w = torch.tensor(j['weights'], dtype=torch.float32); i = 0
        def take(*shape):
            nonlocal i
            n = int(np.prod(shape)); t = w[i:i + n].reshape(*shape); i += n; return t
        self.arrays = []
        for lc in self.cfg['layers']:
            C, K, cin, csz, hs = lc['channels'], lc['kernel_size'], lc['input_size'], lc['condition_size'], lc['head_size']
            gated = lc.get('gated', False); mid = 2 * C if gated else C
            arr = {'re': take(C, cin, 1), 'layers': [], 'C': C, 'gated': gated, 'act': lc.get('activation', 'Tanh')}
            for d in lc['dilations']:
                arr['layers'].append({'d': d, 'cw': take(mid, C, K), 'cb': take(mid), 'mix': take(mid, csz, 1),
                                      'w1': take(C, C, 1), 'b1': take(C)})
            arr['hw'] = take(hs, C, 1); arr['hb'] = take(hs) if lc.get('head_bias', True) else None
            arr['rf'] = sum(d * (K - 1) for d in lc['dilations'])
            self.arrays.append(arr)
        self.head_scale = float(w[i]); i += 1
        assert i == len(w), (i, len(w))
        self.rf = sum(a['rf'] for a in self.arrays) + 1

    @torch.no_grad()
    def __call__(self, x, block=48000 * 8):
        x = np.asarray(x, dtype=np.float32)
        out = np.zeros_like(x)
        pad = self.rf - 1
        xp = np.concatenate([np.zeros(pad, np.float32), x])
        for s in range(0, len(x), block):
            seg = torch.from_numpy(xp[s:s + block + pad])[None, None]
            out[s:s + block] = self._fwd(seg)[0, 0].numpy()[:len(x[s:s + block])]
        return out

    def _fwd(self, x):
        cond = x; y = x; head = None
        for a in self.arrays:
            z = F.conv1d(y, a['re'])
            L = z.shape[2]; out_len = L - a['rf']
            for ly in a['layers']:
                zc = F.conv1d(z, ly['cw'], ly['cb'], dilation=ly['d'])
                z1 = zc + F.conv1d(cond, ly['mix'])[:, :, -zc.shape[2]:]
                if a['gated']:
                    C = a['C']; post = torch.tanh(z1[:, :C]) * torch.sigmoid(z1[:, C:])
                else:
                    post = torch.tanh(z1) if a['act'] == 'Tanh' else F.relu(z1)
                z = z[:, :, -post.shape[2]:] + F.conv1d(post, ly['w1'], ly['b1'])
                ht = post[:, :, -out_len:]
                head = ht if head is None else head[:, :, -out_len:] + ht
            head = F.conv1d(head, a['hw'], a['hb'])
            y = z; cond = cond[:, :, -z.shape[2]:] if False else cond
        return self.head_scale * head


if __name__ == '__main__':
    import sys, soundfile as sf, time
    m = NAM(sys.argv[1]); print('receptive field', m.rf)
    t = np.arange(48000 * 2) / 48000
    x = 0.3 * np.sin(2 * np.pi * 110 * t) * np.exp(-t * 2)
    t0 = time.time(); y = m(x); print('2 s in', round(time.time() - t0, 2), 's; out peak', float(np.abs(y).max()), 'rms', float(np.sqrt((y ** 2).mean())))
