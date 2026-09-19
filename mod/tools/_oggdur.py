# -*- coding: utf-8 -*-
"""读 Ogg Vorbis 时长（不依赖第三方库）：解析最后一个 page 的 granule / 采样率。

用法: python tools\\_oggdur.py 模型\\拉栓上膛.ogg [...]
"""
import io
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def duration(path):
    data = open(path, 'rb').read()
    # 第一页里的 identification header 给出采样率
    i = data.find(b'\x01vorbis')
    rate = struct.unpack_from('<I', data, i + 12)[0]
    # 逐页扫，记住最后一个完成页的 granule
    pos = 0
    gran = 0
    while pos + 27 <= len(data):
        if data[pos:pos + 4] != b'OggS':
            break
        nseg = data[pos + 26]
        head = 27 + nseg
        body = sum(data[pos + 27:pos + 27 + nseg])
        g = struct.unpack_from('<q', data, pos + 6)[0]
        if g >= 0:
            gran = g
        pos += head + body
    return gran / float(rate), rate


for p in sys.argv[1:]:
    if not os.path.exists(p):
        print('!! 找不到 %s' % p)
        continue
    sec, rate = duration(p)
    print('%-34s %6.3f s  (%d Hz, %.1f KB)'
          % (os.path.basename(p), sec, rate, os.path.getsize(p) / 1024.0))
