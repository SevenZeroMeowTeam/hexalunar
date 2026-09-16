#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键推送：**先扫 GitHub 可用 IP → 写 hosts → 再 push**，失败自动重扫重试。

为什么需要它：这台机器 github.com 可用 IP 隔几天就换，全局 git 代理
（127.0.0.1:7897）又经常没开。写死的 hosts 一旦失效，push 会报
`Recv failure: Connection was reset` / `Could not connect to server`。
本脚本每次推送都重扫一遍，选最快的节点。

用法:
  python tools/push.py                     # 扫描 + 推送到 origin 当前分支
  python tools/push.py -m "提交说明"        # 顺便提交所有改动（中文安全，走 UTF-8 文件）
  python tools/push.py --remote origin --branch main
  python tools/push.py --no-commit         # 只扫描 + 推送，不动暂存区
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import github_ip  # noqa: E402  (同目录工具，直接复用扫描逻辑)

# 绕过全局代理 + 强制 HTTP/1.1（代理没开时直连更稳，HTTP/2 在被重置的网络里更容易断）
GIT_OVERRIDES = ["-c", "http.proxy=", "-c", "https.proxy=", "-c", "http.version=HTTP/1.1"]


def run(cmd, check=True, quiet=False):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    if not quiet:
        print(out.rstrip())
    if check and proc.returncode != 0:
        raise SystemExit(f"命令失败({proc.returncode}): {' '.join(cmd)}")
    return proc.returncode, out


def git(*args, check=True, quiet=False):
    return run(["git", *GIT_OVERRIDES, *args], check=check, quiet=quiet)


def commit_all(message):
    """提交说明写进 UTF-8 文件再 -F，避免 PowerShell/Git 的中文编码坑。"""
    msg_path = os.path.join(ROOT, "_push_commit_msg.txt")
    with open(msg_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(message.rstrip() + "\n")
    try:
        git("add", "-A")
        code, out = git("commit", "-F", msg_path, check=False)
        if code != 0 and "nothing to commit" not in out:
            raise SystemExit("提交失败，请检查上面的输出")
    finally:
        if os.path.exists(msg_path):
            os.remove(msg_path)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--message", help="提交说明（给了就先 git add -A 并提交）")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default=None, help="默认取当前分支")
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--no-scan", action="store_true", help="跳过 IP 扫描（调试用）")
    args = ap.parse_args()

    if args.message:
        print(f"[git] 提交改动：{args.message}")
        commit_all(args.message)

    if args.branch is None:
        args.branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
                                     capture_output=True, text=True).stdout.strip()
    print(f"[git] 目标：{args.remote}/{args.branch}")

    for attempt in range(1, args.attempts + 1):
        if not args.no_scan:
            print(f"\n[扫描] 第 {attempt}/{args.attempts} 次探测 GitHub 可用 IP …")
            good = github_ip.scan("github.com")
            if good:
                for ip, cost in good[:5]:
                    print(f"   {ip:16} {cost * 1000:6.0f} ms")
                ok, msg = github_ip.apply_hosts(good[0][0], "github.com")
                print(f"[hosts] {good[0][0]} -> {msg}")
            else:
                print("   [警告] 没扫到可用节点，先按当前网络直接试一次")
        code, out = git("push", args.remote, f"HEAD:refs/heads/{args.branch}", check=False)
        if code == 0:
            print(f"\n[完成] 已推送到 {args.remote}/{args.branch}；CI 会自动构建（见仓库 Actions）")
            return 0
        print("[重试] 本次推送失败，将重新扫描可用 IP 后再试")
    return 1


if __name__ == "__main__":
    sys.exit(main())
