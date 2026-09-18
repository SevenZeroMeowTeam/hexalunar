#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打印若干 Blockbench MCP 工具的 inputSchema（避免 PowerShell 转义地狱）。

用法: python tools/bb_schema_dump.py tool1 tool2 ...
      python tools/bb_schema_dump.py --all            # 只列名字
      python tools/bb_schema_dump.py --find camera    # 名字含关键字的工具
"""
import json
import sys

from bbmcp import Mcp


def main(argv):
    mcp = Mcp().connect()
    tools = {t["name"]: t for t in mcp.tools()}
    names = argv[1:]
    if not names:
        print("用法见文件头")
        return 2
    if names[0] == "--all":
        for n in sorted(tools):
            print(n)
        return 0
    if names[0] == "--find":
        kw = names[1].lower()
        for n in sorted(tools):
            if kw in n.lower():
                print(n)
        return 0
    for n in names:
        t = tools.get(n)
        if not t:
            print("=== %s: 无此工具 ===" % n)
            continue
        print("=== %s ===" % n)
        print((t.get("description") or "").strip()[:600])
        sch = t.get("inputSchema") or {}
        props = sch.get("properties") or {}
        req = set(sch.get("required") or [])
        for k, v in props.items():
            typ = v.get("type")
            if typ == "array":
                typ = "[%s]" % ((v.get("items") or {}).get("type") or "?")
            enum = v.get("enum")
            extra = ""
            if enum:
                extra = " enum=" + ",".join(str(e) for e in enum)
            if v.get("description"):
                extra += "  # " + v["description"].strip().splitlines()[0][:90]
            print("   %s%s: %s%s" % (k, "*" if k in req else "", typ, extra))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
