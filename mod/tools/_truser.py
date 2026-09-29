"""倒出 transcript 里所有 user.message 的纯文本（图片折成 <img>）。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TR = (r'c:\Users\Administrator\AppData\Roaming\Code\User\workspaceStorage'
      r'\4e71f61302ddfc05e86ab3be3d3e2710\GitHub.copilot-chat\transcripts'
      r'\055d7aaa-b2ca-4826-93c8-400cec251225.jsonl')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'build', '_truser.txt')

rows = []
with io.open(TR, 'r', encoding='utf-8', errors='replace') as f:
    for ln in f:
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass

lines = ['records=%d' % len(rows)]
for r in rows:
    t = r.get('type') or ''
    if 'user' not in t.lower():
        continue
    d = r.get('data') or {}
    c = d.get('content')
    if isinstance(c, list):
        bits = []
        for p in c:
            if isinstance(p, dict):
                if str(p.get('type', '')).lower().find('image') >= 0 or 'data' in p:
                    bits.append('<img>')
                else:
                    bits.append(str(p.get('text') or p.get('content') or ''))
            else:
                bits.append(str(p))
        c = ' '.join(bits)
    c = str(c or '')
    if len(c) > 1500:
        c = c[:1500] + '…[len=%d]' % len(c)
    lines.append('### %s : %s' % (t, c.replace('\n', ' ⏎ ')))

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('ok lines=%d' % len(lines))
