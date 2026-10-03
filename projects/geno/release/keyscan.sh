#!/bin/sh
# Scan a checkout for API keys before a commit or push: its working tree (tracked and untracked files) and, if it's a git
# repo, every blob in its whole history (all refs). It prints only the pattern's name and where it matched, never the
# matched text, and exits 1 on any hit.
#   projects/geno/release/keyscan.sh DIR
# Patterns: OpenAI (sk-...), Google/Gemini (AIza...), ElevenLabs (sk_ + 40-64 hex), Hugging Face (hf_...), Higgsfield's
# HF_KEY (an id:secret pair: a UUID or long id, a colon, a long secret), and the env var names given a literal value.
set -u
DIR=${1:?usage: keyscan.sh DIR}
PATS='openai	sk-(proj-|ant-)?[A-Za-z0-9_-]{20,}
gemini	AIza[0-9A-Za-z_-]{35}
elevenlabs	sk_[0-9a-f]{40,64}
huggingface	hf_[A-Za-z0-9]{30,}
higgsfield-id:secret	[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[A-Za-z0-9_-]{20,}
env-with-value	(OPENAI_API_KEY|GEMINI_API_KEY|GOOGLE_API_KEY|ELEVENLABS_API_KEY|ELEVEN_API_KEY|XI_API_KEY|HF_KEY|HF_TOKEN|HIGGSFIELD_[A-Z_]*)[[:space:]]*[=:][[:space:]]*["'"'"']?[A-Za-z0-9_-]{12,}'
hits=0
tab=$(printf '\t')
echo "$PATS" | while IFS="$tab" read -r name re; do
  # the working tree (minus .git)
  n=$(grep -r -I -E -l --exclude-dir=.git -e "$re" "$DIR" 2>/dev/null | wc -l | tr -d ' ')
  files=$(grep -r -I -E -l --exclude-dir=.git -e "$re" "$DIR" 2>/dev/null | sed "s#^$DIR/##" | head -5 | tr '\n' ' ')
  h=0
  if [ -d "$DIR/.git" ]; then
    # every blob reachable from any ref, once each
    h=$(git -C "$DIR" rev-list --all --objects | awk '{print $1}' | git -C "$DIR" cat-file --batch-check='%(objecttype) %(objectname)' |
        awk '$1=="blob"{print $2}' | while read -r b; do git -C "$DIR" cat-file -p "$b" | grep -a -E -q -e "$re" && echo "$b"; done | wc -l | tr -d ' ')
  fi
  printf '%-22s tree %s file(s)%s   history %s blob(s)\n' "$name" "$n" "${files:+: $files}" "$h"
  [ "$n" = 0 ] && [ "$h" = 0 ] || echo HIT >> "${TMPDIR:-/tmp}/keyscan.$$"
done
if [ -f "${TMPDIR:-/tmp}/keyscan.$$" ]; then rm -f "${TMPDIR:-/tmp}/keyscan.$$"; echo "keyscan: HITS (inspect the files named, without printing them)"; exit 1; fi
echo "keyscan: clean"
