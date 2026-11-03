"""本文中の方角・距離・所要時間を、位置データ.json と照合する。

使い方: python scripts/check_rewrite_places.py <ファイルまたはフォルダ> [...]
        --all を付けると、食い違いのない記述も一覧に出す。

同じ文に登録地点が一つだけ出てきて、方角・キロ・日数・時間の記述がある文を調べる。
自動判定は目安。「〇〇の北」のような地点基準の方角は誤検知になるので、目で確かめる。
"""
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rewrite_places as rp  # noqa: E402

KANJI = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
         "六": 6, "七": 7, "八": 8, "九": 9}
TRAVEL = r"かかる|かけて|歩い|歩き|歩け|行程|片道|往復|道のり|距離|着く|着い|到着|で行|まで|ウロジカで|馬で|荷馬車で|の旅"
NUM = r"(?:[0-9０-９]+(?:\.[0-9]+)?|[〇零一二三四五六七八九十百]+)"


def to_num(s):
    s = s.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    if re.fullmatch(r"[0-9.]+", s):
        return float(s)
    total, cur = 0, 0
    for ch in s:
        if ch in KANJI:
            cur = KANJI[ch]
        elif ch == "十":
            total += (cur or 1) * 10
            cur = 0
        elif ch == "百":
            total += (cur or 1) * 100
            cur = 0
    return float(total + cur)


def bearing_of(word):
    return rp.DIRS16.index(word) * 22.5


def angle_diff(a, b):
    return abs((a - b + 180) % 360 - 180)


def expected_days(km, sp):
    return {"徒歩": rp.half(km / sp["徒歩旅_km每日"]),
            "ウロジカ": rp.half(km / sp["ウロジカ_km每日"]),
            "荷馬車": rp.half(km / sp["荷馬車_km每日"])}


def check_sentence(sent, places, sp):
    found = []
    for p in places:
        names = [p["名"]] + p.get("別名", []) + ([p["旧名"]] if p.get("旧名") else [])
        if any(n in sent for n in names):
            found.append((p, names))
    if len(found) != 1:
        return None
    p, names = found[0]
    rest = sent
    for q in places:  # 地点名の中の方角語を除く
        for n in [q["名"]] + q.get("別名", []) + ([q["旧名"]] if q.get("旧名") else []):
            rest = rest.replace(n, "＃")
    issues, claims = [], []
    # 地点を基準にした方角（「＃の北」「＃道から北東」など）は三ツ辻基準ではないので除く
    rel = "|".join(sorted(rp.DIRS16, key=len, reverse=True))
    rest = re.sub(r"＃[道側]?(?:から|より|の|を基準に)(?:" + rel + ")", "＃", rest)
    travel = re.search(TRAVEL, rest) is not None
    words = []
    pat = "|".join(sorted(rp.DIRS16, key=len, reverse=True))
    for m in re.finditer(pat, rest):
        words.append(m.group())
    viewpoint = re.search(r"ここから|そこから|からだと|から見ると|から見て|から見た|から見れば", rest)
    if words:
        claims.append("方角:" + "・".join(words))
        if not viewpoint and all(angle_diff(bearing_of(w), p["方位"]) > 33.75 for w in words):
            issues.append(f"方角（正: {rp.dir16(p['方位'])}）")
    for m in re.finditer(NUM + r"\s*(?:キロ|km|ｋｍ)", rest):
        v = to_num(re.match(NUM, m.group()).group())
        claims.append(m.group())
        if v and abs(v - p["km"]) / p["km"] > 0.15:
            issues.append(f"距離（正: 約{rp.km_str(p['km'])}km）")
    roundtrip = "往復" in rest
    exp = expected_days(p["km"], sp)
    for m in re.finditer(r"(" + NUM + r"|半)日(半)?(?![前目付中])(?!.{0,3}後)", rest):
        if p["km"] <= sp["日帰り上限_km"] or not travel:
            continue
        g = m.group(1)
        v = 0.5 if g == "半" else to_num(g) + (0.5 if m.group(2) else 0)
        claims.append(m.group())
        ok = [x * (2 if roundtrip else 1) for x in exp.values()]
        if all(abs(v - x) > 0.5 for x in ok):
            issues.append("日数（正: " + "、".join(f"{k}{rp.fmt_days(x)}" for k, x in exp.items()) + "）")
    for m in re.finditer(r"(" + NUM + r"|半)時間(半)?", rest):
        if p["km"] > sp["日帰り上限_km"] or not travel:
            continue
        g = m.group(1)
        v = 0.5 if g == "半" else to_num(g) + (0.5 if m.group(2) else 0)
        h = p["km"] / sp[p["地形"]] * (2 if roundtrip else 1)
        claims.append(m.group())
        if abs(v - h) > max(0.5, h * 0.4):
            issues.append(f"時間（正: 片道約{rp.fmt_hours(p['km'] / sp[p['地形']])}）")
    if re.search("(?:" + NUM + "|半)刻(?!み)", rest):
        issues.append("単位「刻」（リライト版は時間・分で書く）")
    if not claims and not issues:
        return None
    return p, claims, issues


def naming_issues(sent, d):
    """見る場所で指す標塔が変わる書き方を拾う（リライト方針書 5-2）。"""
    dirs = "|".join(sorted(rp.DIRS16, key=len, reverse=True))
    towns = "|".join(p["名"] for p in d["地点"] if p["群"] in ("集落", "遠方"))
    found = []
    for m in re.finditer(r"(?:" + towns + r")(?:から見た|から見て|では|の人の|の)(?:" + dirs + r")の(?:標塔|柱)", sent):
        found.append(f"集落基準の方角名「{m.group()}」→ 地の文では三ツ辻での名前を使う")
    for m in re.finditer(r"(?:" + dirs + r")(?:に見える|に立つ|の空の|側の)(?:標塔|柱)", sent):
        found.append(f"方角と標塔を続けた言い方「{m.group()}」→ 名前と紛れる")
    return found


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show_all = "--all" in sys.argv
    if not args:
        sys.exit(__doc__)
    d = rp.load()
    files = []
    for a in args:
        path = Path(a)
        files += sorted(path.rglob("*.md")) if path.is_dir() else [path]
    n_claim = n_issue = 0
    for f in files:
        for ln, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for sent in re.split(r"(?<=[。！？」])", line):
                for m in naming_issues(sent, d):
                    n_issue += 1
                    print(f"[要確認] {f.name}:{ln} 標塔の呼び名 | {m}")
                    print("    " + sent.strip()[:90])
                r = check_sentence(sent, d["地点"], d["速度"])
                if not r:
                    continue
                p, claims, issues = r
                n_claim += 1
                if issues:
                    n_issue += 1
                if issues or show_all:
                    mark = "要確認" if issues else "OK"
                    print(f"[{mark}] {f.name}:{ln} {p['名']} | {'／'.join(claims)}")
                    if issues:
                        print("    → " + "／".join(issues))
                    print("    " + sent.strip()[:90])
    print(f"\n照合した記述 {n_claim} 件、要確認 {n_issue} 件")


if __name__ == "__main__":
    main()
