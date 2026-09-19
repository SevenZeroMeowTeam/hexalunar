# -*- coding: utf-8 -*-
"""Recover the tail of the current Copilot Chat debug log (ASCII-only output)."""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LOG = (r'c:\Users\Administrator\AppData\Roaming\Code\User\workspaceStorage'
       r'\4e71f61302ddfc05e86ab3be3d3e2710\GitHub.copilot-chat\debug-logs'
       r'\f1a57acd-884a-45b5-bbdf-6d50bd599d89\main.jsonl')

path = LOG
if not os.path.exists(path):
    print('no log at', path)
    sys.exit(1)

size = os.path.getsize(path)
print('log size = %.2f MB' % (size / 1048576.0))

data = open(path, 'rb').read().decode('utf-8', 'replace')
lines = data.split('\n')
print('lines =', len(lines))


def window(needle, count, before, after, tag):
    hits = [m.start() for m in re.finditer(re.escape(needle), data)]
    print('\n===== %s : %d hits =====' % (tag, len(hits)))
    for i in hits[-count:]:
        seg = data[max(0, i - before):i + after]
        print('---- [%d] ----' % i)
        print(seg.replace('\\n', '\n'))


window('awp', 3, 2500, 2500, 'awp')
window('AWP', 3, 1200, 1200, 'AWP')
