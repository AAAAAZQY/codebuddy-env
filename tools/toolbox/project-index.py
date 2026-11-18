# -*- coding: gbk -*-
# project-index.py -- build/query a searchable map of a DLP-encrypted project via the bridge.
# All project reads go through the bridge (127.0.0.1:37821) because untrusted-side reads
# get ciphertext; the bridge (trusted) returns plaintext.
#
# Usage:
#   project-index.py --roots
#       print bridge /ping real<->mirror pairs (to learn the real root of a project)
#   project-index.py --build --root <real_root> --name <proj>
#       recurse real_root via /list, fetch .c/.h via /raw, parse symbols + head comment,
#       save D:\Codebuddy\index\<proj>.json  (one-time cost; rebuild when code changes)
#   project-index.py --query --name <proj> --kw <keyword>
#       search index: file paths, function names, declarations
#   project-index.py --around --name <proj> --file <rel_path> --kw <keyword> [--ctx N]
#       fetch the real file via /raw and print +/-N lines around the first match
#       (this is the "fragment fetch" tool: never read_file the whole encrypted file)
import sys, os, json, re, urllib.request, urllib.parse

BRIDGE = "http://127.0.0.1:37821"
INDEX_DIR = r"D:\Codebuddy\index"
FN = re.compile(r'\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{')


def _get(path):
    return urllib.request.urlopen(BRIDGE + path, timeout=30).read()


def list_dir(real):
    d = json.loads(_get("/list?p=" + urllib.parse.quote(real)).decode("utf-8"))
    return d.get("entries", [])


def read_file(real):
    # python is DLP-trusted: read plaintext directly; the file stays encrypted on disk
    with open(real, "rb") as f:
        return f.read()


def walk(real, rel=""):
    out = []
    try:
        for e in list_dir(real):
            name = e["n"]; isdir = e["d"]
            if isdir:
                out += walk(os.path.join(real, name), os.path.join(rel, name))
            else:
                out.append((os.path.join(real, name), os.path.join(rel, name), e["s"]))
    except Exception as ex:
        print("  ! list failed", real, ex)
    return out


def parse(text):
    lines = text.splitlines()
    head = []; started = False
    for ln in lines[:40]:
        s = ln.strip()
        if not s:
            if started:
                break
            continue
        if s.startswith("//") or s.startswith("/*") or s.startswith("*") or s.endswith("*/"):
            head.append(s); started = True
        else:
            if started:
                break
            break
    syms = []
    for idx, ln in enumerate(lines):
        m = FN.search(ln)
        if m:
            decl = lines[idx - 1].strip() if idx > 0 else ""
            syms.append({"n": m.group(1), "l": idx + 1, "d": decl})
    return head, syms


def build(real, name):
    os.makedirs(INDEX_DIR, exist_ok=True)
    files = walk(real)
    idx = {"root": real, "name": name, "files": []}
    n = 0
    for full, relp, size in files:
        ext = os.path.splitext(relp)[1].lower()
        if ext not in (".c", ".h"):
            continue
        if size > 300000:
            print("  skip(large)", relp, size); continue
        try:
            raw = read_file(full)
            try:
                text = raw.decode("utf-8")
            except Exception:
                text = raw.decode("gbk", "replace")
        except Exception as ex:
            print("  ! read failed", relp, ex); continue
        head, syms = parse(text)
        idx["files"].append({"p": relp, "s": size, "h": head, "fns": syms})
        n += 1
    outp = os.path.join(INDEX_DIR, name + ".json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    print("built", name, "files:", n, "->", outp)


def load(name):
    with open(os.path.join(INDEX_DIR, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def query(name, kw):
    idx = load(name)
    kw = kw.lower()
    for fl in idx["files"]:
        hit = kw in fl["p"].lower()
        fns = [s for s in fl["fns"] if kw in s["n"].lower() or kw in s["d"].lower()]
        if hit or fns:
            print("FILE", fl["p"], "(" + str(fl["s"]) + "B)")
            for s in fns[:12]:
                print("   %s  L%d  %s" % (s["n"], s["l"], s["d"][:80]))


def around(name, relp, kw, ctx):
    idx = load(name)
    real = idx["root"]
    full = None
    for fl in idx["files"]:
        if fl["p"] == relp or fl["p"].endswith(relp):
            full = os.path.join(real, fl["p"]); break
    if not full:
        print("not in index:", relp); return
    text = read_file(full).decode("utf-8", "replace")
    lines = text.splitlines()
    target = [i for i, l in enumerate(lines) if kw.lower() in l.lower()]
    if not target:
        print("kw not found:", kw); return
    for l in lines[max(0, target[0] - ctx):target[0] + ctx + 1]:
        print(l)


def roots():
    d = json.loads(_get("/ping").decode("utf-8"))
    for pr in d.get("pairs", []):
        print(pr["real"], " <=> ", pr["mirror"])


def find_index_for(real):
    best = None
    for f in os.listdir(INDEX_DIR):
        if not f.endswith(".json"):
            continue
        idx = load(f[:-5])
        r = idx.get("root", "")
        if r and real.lower().startswith(r.lower()):
            if best is None or len(r) > len(best[1]):
                best = (idx, r)
    return best[0] if best else None


def update_one(real):
    idx = find_index_for(real)
    if not idx:
        return
    relp = os.path.relpath(real, idx["root"]).replace("\\", "/")
    ext = os.path.splitext(real)[1].lower()
    idx["files"] = [fl for fl in idx["files"] if fl["p"] != relp]
    if ext in (".c", ".h"):
        try:
            raw = read_file(real)
            try:
                text = raw.decode("utf-8")
            except Exception:
                text = raw.decode("gbk", "replace")
            head, syms = parse(text)
            idx["files"].append({"p": relp, "s": len(raw), "h": head, "fns": syms})
        except Exception as ex:
            print("  ! update read failed", relp, ex)
    outp = os.path.join(INDEX_DIR, idx["name"] + ".json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    print("index updated", idx["name"], relp)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    if cmd == "--roots":
        roots()
    elif cmd == "--build":
        real = a[a.index("--root") + 1]
        name = a[a.index("--name") + 1] if "--name" in a else os.path.basename(real.rstrip("\\/"))
        build(real, name)
    elif cmd == "--query":
        query(a[a.index("--name") + 1], a[a.index("--kw") + 1])
    elif cmd == "--around":
        name = a[a.index("--name") + 1]; relp = a[a.index("--file") + 1]; kw = a[a.index("--kw") + 1]
        ctx = int(a[a.index("--ctx") + 1]) if "--ctx" in a else 5
        around(name, relp, kw, ctx)
    elif cmd == "--update":
        update_one(a[a.index("--path") + 1])
    elif cmd == "--list":
        print(os.listdir(INDEX_DIR))
    else:
        print("unknown cmd", cmd)


if __name__ == "__main__":
    main()
