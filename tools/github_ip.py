#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub 可用 IP 扫描（TCP 连通 + 真 TLS 握手双重验证）。

背景：这台机器上 github.com 的可用 IP 隔几天就变，hosts 里写死的旧 IP 失效后
git 会直接 `Connection was reset` / `Could not connect`。所以每次推送前先扫一遍：
TCP 通只代表端口开着，必须再做一次 SNI=github.com 的 TLS 握手才是真能用的节点。

用法:
  python tools/github_ip.py                 # 扫描 + 打印排名
  python tools/github_ip.py --apply         # 顺便把最快节点写进 hosts（自动备份 + flushdns）
  python tools/github_ip.py --host api.github.com --apply   # 换域名

退出码: 0 有可用节点 / 1 全部不可用（多半是网络本身断了，或该开代理了）
"""
import argparse
import concurrent.futures
import os
import re
import socket
import ssl
import subprocess
import sys
import time

HOSTS = r"C:\Windows\System32\drivers\etc\hosts"

# GitHub 常见入口 IP（历史实测可用过的都留着，扫一遍很快）
CANDIDATES = [
    "140.82.112.3", "140.82.112.4", "140.82.112.5",
    "140.82.113.3", "140.82.113.4", "140.82.113.5",
    "140.82.114.3", "140.82.114.4", "140.82.114.5",
    "140.82.116.3", "140.82.116.4",
    "140.82.121.3", "140.82.121.4",
    "20.205.243.166", "20.27.177.113", "20.200.245.247", "20.201.28.151",
    "20.207.73.82", "20.233.83.145", "20.248.137.48", "20.26.156.215",
    "20.29.134.23", "20.199.39.232", "20.217.135.5", "4.237.22.38",
]


def tcp_ok(ip, timeout=4.0):
    try:
        with socket.create_connection((ip, 443), timeout=timeout):
            return True
    except OSError:
        return False


def https_ok(ip, host, timeout=8.0, attempts=2):
    """真做一次 TLS 握手 + HEAD，返回耗时（秒）；失败返回 None。

    网络干扰是阵发性的（同一天 curl 会 200/000 交替），所以默认重试 2 次，
    只要有一次成功就算该节点可用。
    """
    for attempt in range(attempts):
        start = time.time()
        try:
            ctx = ssl.create_default_context()
            raw = socket.create_connection((ip, 443), timeout=timeout)
            tls = ctx.wrap_socket(raw, server_hostname=host)
            tls.sendall(f"HEAD / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
            head = tls.recv(120)
            tls.close()
            if b"HTTP/1." in head:
                return time.time() - start
        except Exception:  # noqa: BLE001  —— 网络异常种类多，统一当失败
            pass
    return None


def scan(host="github.com", ips=None, workers=16):
    """返回 [(ip, 耗时秒)]，按耗时升序。"""
    ips = ips or CANDIDATES
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        alive = [ip for ip, ok in zip(ips, pool.map(lambda i: tcp_ok(i), ips)) if ok]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(zip(alive, pool.map(lambda i: https_ok(i, host), alive)))
    return sorted((r for r in results if r[1]), key=lambda r: r[1])


def current_hosts_ip(host="github.com"):
    """当前 hosts 里给这个域名写的 IP（没有则 None）——扫描全挂时可用来先对付一下。"""
    try:
        with open(HOSTS, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[1].lower() == host.lower():
                    return parts[0]
    except OSError:
        pass
    return None


def apply_hosts(ip, host="github.com"):
    """把 host 指向 ip；返回 (是否成功, 说明)。"""
    if not os.path.exists(HOSTS):
        return False, f"找不到 {HOSTS}"
    try:
        with open(HOSTS, "r", encoding="utf-8", errors="replace") as f:
            original = f.read()
    except OSError as exc:
        return False, f"读取 hosts 失败: {exc}"

    backup = HOSTS + ".ipscanbak"
    try:
        if not os.path.exists(backup):
            with open(backup, "w", encoding="utf-8") as f:
                f.write(original)
    except OSError:
        pass  # 备份失败不阻塞主流程

    lines = original.splitlines()
    pattern = re.compile(r"^\s*[\d.]+\s+" + re.escape(host) + r"\s*$", re.I)
    out, replaced = [], False
    for line in lines:
        if pattern.match(line):
            out.append(f"{ip} {host}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{ip} {host}")

    try:
        with open(HOSTS, "w", encoding="utf-8", errors="replace") as f:
            f.write("\n".join(out) + "\n")
    except OSError as exc:
        return False, f"写入 hosts 失败（多半需要管理员权限）: {exc}"

    subprocess.run(["ipconfig", "/flushdns"], capture_output=True, check=False)
    return True, ("已更新" if replaced else "已追加")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="github.com")
    ap.add_argument("--apply", action="store_true", help="把最快的节点写入 hosts")
    args = ap.parse_args()

    print(f"[扫描] {args.host} 的候选节点 {len(CANDIDATES)} 个（TCP + TLS 双重验证，各重试 2 次）…")
    good = scan(args.host)
    if not good:
        now = current_hosts_ip(args.host)
        hint = ""
        if now:
            hint = f"（hosts 当前指向 {now}，可以直接先试一次 push）"
        print("[结果] 本轮没扫到能完成 HTTPS 的节点" + hint)
        print("       网络阵发性抖动时属正常，重跑一次即可；若代理软件在运行，"
              "也可 `git -c http.proxy=http://127.0.0.1:7897 push`")
        return 1

    print(f"[结果] 可用节点 {len(good)} 个：")
    for ip, cost in good:
        print(f"   {ip:16} {cost * 1000:7.0f} ms")

    if args.apply:
        ip = good[0][0]
        ok, msg = apply_hosts(ip, args.host)
        print(f"[hosts] {ip} {args.host} -> {msg}")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
