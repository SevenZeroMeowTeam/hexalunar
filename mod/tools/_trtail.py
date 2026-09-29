"""把 transcript 里最后 N 条消息的**纯文本**倒出来（跳过 base64 图片）。

终端按 GBK 显示中文会乱码，所以结果写到 build/_trtail.txt，用编辑器看。
"""
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
N = 24
LIM = 900


def txt(part):
    """从一条 content part 里抽纯文本；图片/base64 一律折叠成 <img>。"""
    if isinstance(part, str):
        return part
    if not isinstance(part, dict):
        return ''
    t = part.get('type') or part.get('kind') or ''
    if 'image' in str(t).lower() or 'data' in part and isinstance(part.get('data'), str):
        return '<img>'
    for k in ('text', 'content', 'value', 'message'):
        v = part.get(k)
        if isinstance(v, str):
            if len(v) > 4000 and all(c.isalnum() or c in '+/=\n' for c in v[:200]):
                return '<b64>'
            return v
        if isinstance(v, list):
            return ' | '.join(x for x in (txt(i) for i in v) if x)
    return ''


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

lines = []
lines.append('records=%d' % len(rows))
for r in rows[-N:]:
    kind = r.get('type') or r.get('role') or '?'
    v = r.get('v') if isinstance(r.get('v'), dict) else r
    role = v.get('role') or v.get('message', {}).get('role') if isinstance(v.get('message'), dict) else v.get('role')
    parts = v.get('content') or v.get('parts') or []
    if isinstance(parts, str):
        parts = [parts]
    body = ' | '.join(x for x in (txt(p) for p in parts) if x)
    if len(body) > LIM:
        body = body[:LIM] + '…[%d]' % len(body)
    lines.append('--- [%s/%s] %s' % (kind, role, body.replace('\n', ' ⏎ ')))

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('wrote %s  records=%d' % (OUT, len(rows)))
