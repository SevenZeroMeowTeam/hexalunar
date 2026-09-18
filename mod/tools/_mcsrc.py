"""从 Forge 源码 jar 里抽出第一人称手臂相关代码（离线查证用）。

用法: python tools/_mcsrc.py ItemInHandRenderer renderPlayerArm 40
      python tools/_mcsrc.py PlayerRenderer renderHand 40
"""
import io
import sys
import zipfile

JAR = (r"C:\Users\Administrator\.gradle\caches\forge_gradle\minecraft_user_repo\net"
       r"\minecraftforge\forge\1.20.1-47.4.0_mapped_official_1.20.1"
       r"\forge-1.20.1-47.4.0_mapped_official_1.20.1-sources.jar")


def main(argv):
    cls = argv[1]
    keyword = argv[2] if len(argv) > 2 else "renderPlayerArm"
    span = int(argv[3]) if len(argv) > 3 else 30
    with zipfile.ZipFile(JAR) as z:
        name = None
        for n in z.namelist():
            if n.endswith("/%s.java" % cls):
                name = n
                break
        if name is None:
            print("找不到 %s.java" % cls)
            return
        text = z.read(name).decode("utf-8", "replace")
    lines = text.splitlines()
    hits = [i for i, ln in enumerate(lines) if keyword in ln]
    print("== %s: %d 处命中 '%s' ==" % (cls, len(hits), keyword))
    for i in hits:
        lo = max(0, i - 3)
        hi = min(len(lines), i + span)
        print("\n----- 行 %d -----" % (i + 1))
        for j in range(lo, hi):
            print("%5d| %s" % (j + 1, lines[j]))


if __name__ == "__main__":
    main(sys.argv)
