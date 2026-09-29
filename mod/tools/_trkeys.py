"""看 transcript 记录结构 + 倒出带文本的字段（跳过 base64）。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TR = (r'c:\Users\Administrator\AppData\Roaming\Code\User\workspaceStorage'
      r'\4e71f61302ddfc05e86ab3be3d3e2710\GitHub.copilot-chat\transcripts'
      r'\055d7aaa-b2ca-4826-93c8-400cec251225.jsonl')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'build', '_trtail.txt')

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


def walk(o, depth=0, out=None):
    if out is None:
        out = []
    if depth > 6:
        return out
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('data', 'base64', 'image', 'url', 'blob') and isinstance(v, str):
                continue
            out.append(('  ' * depth) + str(k) + ' :: ' + type(v).__name__)
            walk(v, depth + 1, out)
    elif isinstance(o, list):
        out.append(('  ' * depth) + '[%d]' % len(o))
        for v in o[:3]:
            walk(v, depth + 1, out)
    return out


lines = ['records=%d' % len(rows)]
for i, r in enumerate(rows[-40:]):
    lines.append('=========== #%d  %s' % (i, r.get('type')))
    lines.extend(walk(r))

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('ok %d' % len(rows))
