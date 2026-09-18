"""从 PowerShell 重定向出来的构建日志里，把某段错误上下文打出来（日志可能是 UTF-16）。

用法: python tools/_logctx.py <日志> <关键字> [后几行]
"""
import io
import sys


def main(argv):
    path = argv[1]
    needle = argv[2]
    after = int(argv[3]) if len(argv) > 3 else 4
    raw = open(path, 'rb').read()
    enc = 'utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8'
    text = raw.decode(enc, 'replace').replace('\x00', '')
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if needle in line:
            print('--- line %d' % (i + 1))
            print('\n'.join(lines[i:i + after]))


if __name__ == '__main__':
    main(sys.argv)
