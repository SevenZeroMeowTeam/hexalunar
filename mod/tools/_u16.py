# -*- coding: utf-8 -*-
"""把 PowerShell 重定向出来的 UTF-16 文本转成 UTF-8，方便 read_file / grep 看。

用法::  python tools/_u16.py build/_m1diff.txt [build/_m1diff_u8.txt]
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'build/_m1diff.txt'
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + '_u8.txt'
    raw = open(os.path.join(ROOT, src), 'rb').read()
    enc = 'utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8'
    if enc == 'utf-8':
        for cand in ('utf-8-sig', 'gbk', 'utf-16'):
            try:
                text = raw.decode(cand)
                enc = cand
                break
            except Exception:
                continue
        else:
            text = raw.decode('utf-8', 'replace')
    else:
        text = raw.decode(enc)
    out = os.path.join(ROOT, dst)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(text)
    print('enc=%s bytes=%d -> %s lines=%d' % (enc, len(raw), dst,
                                              text.count('\n') + 1))


if __name__ == '__main__':
    main()
