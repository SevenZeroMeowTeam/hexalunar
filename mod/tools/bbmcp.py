#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Blockbench MCP 桥接工具。

VS Code 里部分 Blockbench MCP 工具被禁用，但 Blockbench 的 MCP 插件本身是一个
本地 HTTP (Streamable HTTP) 服务，可以直接用 JSON-RPC 调它，工具集完全一样。

用法:
  python tools/bbmcp.py list                       # 列出全部工具名
  python tools/bbmcp.py call <tool> '<json>'       # 调一次
  python tools/bbmcp.py batch <calls.json>         # 批量调用, 文件形如 [{"tool":"..","args":{..}}, ..]
  python tools/bbmcp.py schema <tool>              # 打印某个工具的 inputSchema
"""
import json
import sys
import urllib.request

ENDPOINT = "http://localhost:3000/bb-mcp"
PROTOCOL = "2025-06-18"


class Mcp:
    def __init__(self, endpoint=ENDPOINT):
        self.endpoint = endpoint
        self.sid = None
        self._id = 0

    def _post(self, payload):
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL,
        }
        if self.sid:
            headers["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.endpoint, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=600) as resp:
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self.sid = sid
            body = resp.read().decode("utf-8", "replace")
        return self._parse(body)

    @staticmethod
    def _parse(body):
        body = body.strip()
        if not body:
            return None
        # 服务端可能回 SSE (event: message / data: {...})
        if body.startswith("event:") or body.startswith("data:"):
            for line in body.splitlines():
                if line.startswith("data:"):
                    body = line[5:].strip()
                    break
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"_raw": body}

    def _call(self, method, params):
        self._id += 1
        return self._post({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})

    def connect(self):
        self._call("initialize", {
            "protocolVersion": PROTOCOL,
            "capabilities": {},
            "clientInfo": {"name": "bbmcp-bridge", "version": "1.0"},
        })
        # notifications/initialized 是通知, 无 id
        try:
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        except Exception:
            pass
        return self

    def tools(self):
        return self._call("tools/list", {}).get("result", {}).get("tools", [])

    def call(self, name, args):
        res = self._call("tools/call", {"name": name, "arguments": args or {}})
        if "error" in res and res["error"]:
            return {"ok": False, "error": res["error"]}
        result = res.get("result", {})
        text_parts = []
        images = []
        for item in result.get("content", []) or []:
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif item.get("type") == "image":
                images.append(item)
        if images:
            import base64
            import os
            os.makedirs("build/bbshots", exist_ok=True)
            saved = []
            for idx, img in enumerate(images):
                ext = "png" if "png" in (img.get("mimeType") or "") else "bin"
                path = "build/bbshots/shot_%s.%s" % (name, ext)
                with open(path, "wb") as fh:
                    fh.write(base64.b64decode(img.get("data", "")))
                saved.append(os.path.abspath(path))
            text_parts.append("saved:" + ",".join(saved))
        return {
            "ok": not result.get("isError", False),
            "isError": bool(result.get("isError", False)),
            "text": "\n".join(text_parts),
            "structured": result.get("structuredContent"),
        }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    mcp = Mcp().connect()
    cmd = argv[1]

    if cmd == "list":
        for t in mcp.tools():
            print(t["name"])
        return 0

    if cmd == "schema":
        for t in mcp.tools():
            if t["name"] == argv[2]:
                print(json.dumps(t.get("inputSchema", {}), ensure_ascii=False, indent=2))
                return 0
        print("no such tool: " + argv[2])
        return 1

    if cmd == "call":
        name = argv[2]
        args = json.loads(argv[3]) if len(argv) > 3 else {}
        out = mcp.call(name, args)
        print(json.dumps(out, ensure_ascii=False, indent=1)[:20000])
        return 0 if out.get("ok") else 1

    if cmd == "js":
        # 把 .js 文件内容当作 risky_eval 的 code 传进去（绕开命令行转义地狱）
        with open(argv[2], "r", encoding="utf-8") as fh:
            code = fh.read()
        out = mcp.call("risky_eval", {"code": code})
        print(json.dumps(out, ensure_ascii=False, indent=1)[:30000])
        return 0 if out.get("ok") else 1

    if cmd == "batch":
        with open(argv[2], "r", encoding="utf-8") as fh:
            calls = json.load(fh)
        results = []
        for item in calls:
            out = mcp.call(item["tool"], item.get("args", {}))
            out["tool"] = item["tool"]
            results.append(out)
            flag = "OK " if out.get("ok") else "ERR"
            text = (out.get("text") or json.dumps(out.get("error"), ensure_ascii=False))[:300]
            print("%s %-28s %s" % (flag, item["tool"], text.replace("\n", " ")))
        with open("build/bbmcp_last.json", "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=1)
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
