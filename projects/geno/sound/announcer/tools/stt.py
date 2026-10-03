import whisper, sys, glob, os, warnings, json
warnings.filterwarnings('ignore')
model_name = os.environ.get('WMODEL', 'small.en')
m = whisper.load_model(model_name, device='cpu')
files = []
for a in sys.argv[1:]:
    files += sorted(glob.glob(a)) if any(c in a for c in '*?') else [a]
res = {}
for f in files:
    kw = dict(fp16=False, language='en', temperature=0.0)
    if os.environ.get('PROMPT'): kw['initial_prompt'] = os.environ['PROMPT']
    r = m.transcribe(f, **kw)
    res[os.path.basename(f)] = r['text'].strip()
    print(f"{os.path.basename(f)}\t{r['text'].strip()}", flush=True)
