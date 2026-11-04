"""リライト版の本文に、用語の読み.md の表どおり各話の初出にルビを付ける。

使い方: python scripts/add_rewrite_ruby.py <話のファイルかフォルダ> [--dry]
ルビの書き方は ｜漢字《よみ》。見出し行には付けない。すでにルビの付いた名前は数える。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "辺境拠点日誌_リライト" / "設定" / "用語の読み.md"
RUBY = re.compile(r"｜([^《｜]+)《([^》]*)》")


def load_table():
    terms = []
    for line in TABLE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([ぁ-んー]+)\s*\|", line)
        if m:
            terms.append((m.group(1), m.group(2)))
    # 長い名前を先に（小型深淵鰐 を 深淵鰐 より先に）
    terms.sort(key=lambda t: -len(t[0]))
    return terms


def groups(terms):
    """部分一致する名前を同じ組にする（深淵鰐 と 小型深淵鰐）。"""
    out = []
    for name, yomi in terms:
        for g in out:
            if any(name in n or n in name for n, _ in g):
                g.append((name, yomi))
                break
        else:
            out.append([(name, yomi)])
    return out


def process(text, term_groups):
    lines = text.split("\n")
    added = []
    for g in term_groups:
        names = [n for n, _ in g]
        # すでにルビがある組は飛ばす
        if any(m.group(1) in names for line in lines for m in RUBY.finditer(line)):
            continue
        best = None
        for i, line in enumerate(lines):
            if line.startswith("#"):
                continue
            plain_spans = []
            pos = 0
            for m in RUBY.finditer(line):
                plain_spans.append((pos, m.start()))
                pos = m.end()
            plain_spans.append((pos, len(line)))
            for name, yomi in g:
                for a, b in plain_spans:
                    j = line.find(name, a, b)
                    if j != -1 and j + len(name) <= b:
                        cand = (i, j, name, yomi)
                        if best is None or (cand[0], cand[1], -len(name)) < (best[0], best[1], -len(best[2])):
                            best = cand
                        break
            if best is not None and best[0] == i:
                break
        if best:
            i, j, name, yomi = best
            lines[i] = lines[i][:j] + f"｜{name}《{yomi}》" + lines[i][j + len(name):]
            added.append(name)
    return "\n".join(lines), added


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    tg = groups(load_table())
    files = []
    for a in args:
        p = Path(a)
        files += sorted(p.rglob("*.md")) if p.is_dir() else [p]
    for f in files:
        text = f.read_text(encoding="utf-8")
        new, added = process(text, tg)
        print(f"{f.name}: {'、'.join(added) if added else '（なし）'}")
        if not dry and new != text:
            f.write_text(new, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
