"""跑 gradlew compileJava 并只打印关键行（编译错误/警告提到 .java: 行，最后一行是 BUILD 结果）。

绕过 PowerShell 管道偶发吞输出的问题：用 python 起子进程自己过滤。
用法: python tools/_check.py [额外 gradle 任务，默认 compileJava]
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    task = argv[1] if len(argv) > 1 else 'compileJava'
    p = subprocess.run(['cmd', '/c', 'gradlew.bat', task, '--console=plain'],
                       cwd=ROOT, capture_output=True, text=True, errors='replace')
    text = (p.stdout or '') + (p.stderr or '')
    for line in text.splitlines():
        if '.java:' in line or 'BUILD' in line or 'FAIL' in line:
            print(line.rstrip())
    print('exit=%d' % p.returncode)


if __name__ == '__main__':
    main(sys.argv)
