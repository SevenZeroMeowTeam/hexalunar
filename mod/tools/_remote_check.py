# -*- coding: utf-8 -*-
"""复核远端 main 的 sha 与最近几次 CI 运行（匿名可读）——推送脚本的 ls-remote 校验
有时因为 hosts 刚换 IP 而拿不到结果，用它独立确认「到底推上去了没有」。

用法::  python tools/_remote_check.py
"""
import io
import json
import os
import ssl
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(os.path.dirname(HERE), 'build')
REPO = 'SevenZeroMeowTeam/hexalunar'

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def api(path):
    req = urllib.request.Request('https://api.github.com/' + path,
                                 headers={'User-Agent': 'hlc-check',
                                          'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
        return json.load(r)


def main():
    out = []
    try:
        c = api('repos/%s/commits/main' % REPO)
        out.append('远端 main = %s' % c['sha'])
        out.append('  %s' % c['commit']['message'].splitlines()[0])
        out.append('  %s' % c['commit']['committer']['date'])
    except Exception as e:                                   # noqa: BLE001
        out.append('!! commits/main 取不到：%r' % (e,))
    try:
        runs = api('repos/%s/actions/runs?per_page=4' % REPO)['workflow_runs']
        out.append('最近 CI 运行：')
        for r in runs:
            out.append('  #%-4s %-9s %-14s %s' % (r['run_number'], r['status'],
                                                  r['conclusion'], r['head_sha'][:7]))
    except Exception as e:                                   # noqa: BLE001
        out.append('!! actions/runs 取不到：%r' % (e,))
    text = '\n'.join(out)
    with io.open(os.path.join(BUILD, '_remote.txt'), 'w', encoding='utf-8',
                 newline='\n') as fh:
        fh.write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
