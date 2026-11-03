"""リライト版の位置データ(JSON)から、位置台帳(md)と縮尺どおりの地図(SVG)を作る。

使い方: python scripts/rewrite_places.py
入力:  辺境拠点日誌_リライト/設定/位置データ.json
出力:  辺境拠点日誌_リライト/設定/位置台帳.md, 位置地図.svg
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "辺境拠点日誌_リライト" / "設定"
DATA = DIR / "位置データ.json"

DIRS16 = ["北", "北北東", "北東", "東北東", "東", "東南東", "南東", "南南東",
          "南", "南南西", "南西", "西南西", "西", "西北西", "北西", "北北西"]


R3 = math.sqrt(3)
# 中央の六角形のまわりの六角形の名前（中央の六角形の中心から見た方角）
HEX_NAMES = {(0, 0): "中央"}


def hex_centers(n=5):
    """平らな辺が上下に来る六角形の中心（単位：辺の長さ）。"""
    out = []
    for q in range(-n, n + 1):
        for r in range(-n, n + 1):
            out.append((1.5 * q, R3 * (r + q / 2)))
    return out


def gen_lattice(d):
    """格子から標塔（六角形の頂点）を作り、三ツ辻基準の座標を付ける。"""
    g = d["格子"]
    s, (bx, by) = g["辺_km"], g["三ツ辻"]
    verts = {}
    for cx, cy in hex_centers():
        for k in range(6):
            a = math.radians(60 * k)
            v = (round(cx + math.cos(a), 4), round(cy + math.sin(a), 4))
            verts[(round(v[0], 2), round(v[1], 2))] = v
    letters = {tuple(round(c, 2) for c in pos): key for key, pos in g["図記号"].items()}
    pillars = []
    for key, (vx, vy) in verts.items():
        x, y = (vx - bx) * s, (vy - by) * s
        km = math.hypot(x, y)
        if km > g["範囲_km"]:
            continue
        sym = letters.get(key, "")
        name = g["標塔名"].get(sym) or (f"標塔{sym}" if sym else "")
        pillars.append({"名": name, "記号": sym, "群": "標塔" if sym in g["標塔名"] else "標塔（無名）",
                        "注": g.get("標塔注", {}).get(sym, ""),
                        "方位": math.degrees(math.atan2(x, y)) % 360, "km": km, "地形": "野",
                        "x": x, "y": y, "u": (vx, vy)})
    missing = set(g["図記号"]) - {p["記号"] for p in pillars}
    if missing:
        sys.exit(f"図記号が格子の頂点に乗っていない、または範囲外: {sorted(missing)}")
    return pillars


def hex_of(d, x, y):
    """三ツ辻基準の座標(km)が入っている六角形の名前を返す。"""
    g = d["格子"]
    u = (g["三ツ辻"][0] + x / g["辺_km"], g["三ツ辻"][1] + y / g["辺_km"])
    c = min(hex_centers(), key=lambda c: math.dist(c, u))
    if math.dist(c, (0, 0)) < 0.01:
        return "中央"
    b = math.degrees(math.atan2(c[0], c[1])) % 360
    ring = "" if math.dist(c, (0, 0)) < R3 + 0.01 else "外側の"
    return ring + dir16(b)


def load():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    for p in d["地点"]:
        r = math.radians(p["方位"])
        p["x"] = p["km"] * math.sin(r)
        p["y"] = p["km"] * math.cos(r)
    d["標塔"] = gen_lattice(d)
    d["地点"] += [p for p in d["標塔"] if p["名"]]
    return d


def dir16(bearing):
    return DIRS16[int(((bearing % 360) + 11.25) // 22.5) % 16]


def half(v):
    return max(0.5, round(v * 2) / 2)


def fmt_days(v):
    if v == 0.5:
        return "半日"
    whole = int(v)
    return f"{whole}日半" if v - whole else f"{whole}日"


def fmt_hours(h):
    if h < 1:
        m = max(5, int(round(h * 60 / 5) * 5))
        return f"{m}分"
    h = half(h)
    whole = int(h)
    return f"{whole}時間半" if h - whole else f"{whole}時間"


def travel(km, terrain, sp):
    """(徒歩, ウロジカ, 荷馬車) の片道表記を返す。"""
    if km <= sp["日帰り上限_km"]:
        walk = fmt_hours(km / sp[terrain])
        return walk, "-", "-"
    days = half(km / sp["徒歩旅_km每日"])
    nights = math.ceil(days) - 1
    walk = f"{fmt_days(days)}（野営{nights}泊）" if nights else fmt_days(days)
    uro = fmt_days(half(km / sp["ウロジカ_km每日"]))
    cart = fmt_days(half(km / sp["荷馬車_km每日"]))
    return walk, uro, cart


def pair(a, b):
    dx, dy = b["x"] - a["x"], b["y"] - a["y"]
    km = math.hypot(dx, dy)
    bearing = math.degrees(math.atan2(dx, dy)) % 360
    return km, bearing


def km_str(km):
    return f"{km:.1f}" if km < 10 else f"{km:.0f}"


DIRS8 = ["北", "北東", "東", "南東", "南", "南西", "西", "北西"]


def dir8(bearing):
    return DIRS8[int(((bearing % 360) + 22.5) // 45) % 8]


def seg_dist(p, a, b):
    """点pと線分abの最短距離と、そのときのaからの距離。"""
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    L2 = (bx - ax) ** 2 + (by - ay) ** 2
    t = max(0.0, min(1.0, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / L2))
    q = (ax + t * (bx - ax), ay + t * (by - ay))
    return math.dist(p, q), t * math.sqrt(L2)


def viewpoint_section(d):
    """集落から見た標塔の方角と、地元の呼び名が三ツ辻の呼び名とぶつかる組。"""
    named = [p for p in d["標塔"] if p["群"] == "標塔"]
    canon = {p["名"]: p for p in named}
    views = [{"名": "三ツ辻", "x": 0.0, "y": 0.0}] + [p for p in d["地点"] if p["群"] == "集落"]
    out = ["## 見る場所によって変わる標塔の方角（呼び名の注意）", "",
           "地の文では、標塔は「名前」の列の呼び名だけを使う。名前は三ツ辻から見た方角で付けてあり、"
           "どこにいても変えない。下の表は、各集落から見た方角と、その集落の人が方角で呼んだときの言い方。"
           "「衝突」は、その言い方が三ツ辻での別の標塔の名前と同じになる組。台詞で使うときは、"
           "直後の地の文で三ツ辻での名前を示す。", ""]
    for v in views:
        out += [f"### {v['名']}から", "",
                "| 名前（三ツ辻での呼び名） | 図記号 | 方角 | 距離 | 方角で呼ぶと | 衝突 |",
                "|---|---|---|---|---|---|"]
        for p in sorted(named, key=lambda p: math.dist((v["x"], v["y"]), (p["x"], p["y"]))):
            km, br = pair(v, p)
            local = dir8(br) + "の標塔"
            clash = canon.get(local)
            mark = f"**衝突：三ツ辻の{clash['名']}（{clash['記号']}）と同じ**" if clash and clash is not p else ""
            out.append(f"| {p['名']} | {p['記号']} | {dir16(br)} | 約{km_str(km)}km | {local} | {mark} |")
        if v["名"] != "三ツ辻":
            near = min(d["標塔"], key=lambda p: math.dist((v["x"], v["y"]), (p["x"], p["y"])))
            out += ["", f"{v['名']}に一番近い標塔：{near['名'] or near['記号']}（{near['記号']}）"
                        f" 約{km_str(math.dist((v['x'], v['y']), (near['x'], near['y'])))}km"]
            rows = []
            for p in named:
                dist, along = seg_dist((p["x"], p["y"]), (v["x"], v["y"]), (0.0, 0.0))
                if dist <= 20:
                    rows.append(f"| {p['名']} | {p['記号']} | 約{km_str(dist)}km | {v['名']}から約{km_str(along)}km の地点 |")
            if rows:
                out += ["", f"{v['名']}から三ツ辻へまっすぐ向かう道中で近くを通る標塔（20km以内）：", "",
                        "| 名前 | 図記号 | 最接近距離 | 最接近する場所 |", "|---|---|---|---|"] + rows
        out.append("")
    return out


def write_md(d):
    sp = d["速度"]
    pts = {p["名"]: p for p in d["地点"]}
    out = ["# 位置台帳（リライト版）", "",
           "**このファイルは自動生成。直接編集しない。** 正は `位置データ.json`。"
           "編集後に `python scripts/rewrite_places.py` を実行する。", "",
           "方角・距離・所要時間は、本文に書く前に必ずこの表から引く。"
           "表にない場所を書くときは、先に位置データ.json に登録する。", "",
           "## 移動の速さ（共通モデル）", "",
           f"- 日帰り圏（{sp['日帰り上限_km']}km以内）：道 時速{sp['道']}km、野 {sp['野']}km、丘・森 {sp['森']}km",
           f"- 泊まりがけ：徒歩 1日{sp['徒歩旅_km每日']}km、ウロジカ 1日{sp['ウロジカ_km每日']}km、"
           f"荷馬車 1日{sp['荷馬車_km每日']}km",
           "- 所要時間はすべて三ツ辻からの片道。往復は二倍、現地での作業時間は別に足す",
           "- 迂回や悪天候で日数を延ばすときは、本文に理由を書く", ""]
    g = d["格子"]
    out += ["## 標塔の配置", "",
            f"- 標塔は六角形を敷き詰めたときの頂点に立つ。辺（隣の標塔までの距離）は約{g['辺_km']}km",
            "- 位置は格子から自動で計算する。手で置かない",
            "- 「図記号」は作者の図（辺境拠点日誌/設定/三ツ辻拠点.png）の記号",
            "- 「六角形」は、その地点が入っている六角形。中央＝三ツ辻のある六角形（A・C・D・B・E・F）。"
            "ほかは中央の六角形から見た方角で呼ぶ", ""]
    for group in ["近場", "標塔", "集落", "遠方"]:
        out += [f"## {group}", "",
                "| 場所 | 図記号 | 方角 | 距離 | 徒歩片道 | ウロジカ | 荷馬車 | 六角形 | 旧名 | 注 |",
                "|---|---|---|---|---|---|---|---|---|---|"]
        for p in sorted([p for p in d["地点"] if p["群"] == group], key=lambda p: p["km"]):
            w, u, c = travel(p["km"], p["地形"], sp)
            out.append(f"| {p['名']} | {p.get('記号', '')} | {dir16(p['方位'])} | 約{km_str(p['km'])}km "
                       f"| 約{w} | {u} | {c} | {'頂点' if p.get('記号') else hex_of(d, p['x'], p['y'])} "
                       f"| {p.get('旧名', '')} | {p.get('注', '')} |")
        out.append("")
    out += [f"## 範囲内（{g['範囲_km']}km）のすべての標塔", "",
            "名前のない標塔は、本文で使う前に位置データ.json の「標塔名」で名前を付ける。", "",
            "| 図記号 | 名前 | 方角 | 距離 |", "|---|---|---|---|"]
    for p in sorted(d["標塔"], key=lambda p: p["km"]):
        out.append(f"| {p['記号'] or '（図の外）'} | {p['名']} | {dir16(p['方位'])}（{p['方位']:.0f}°） "
                   f"| 約{km_str(p['km'])}km |")
    out.append("")
    out += viewpoint_section(d)
    out += ["## 地点どうしの位置関係", "",
            "| 起点 | 目的地 | 目的地の方角 | 直線距離 |", "|---|---|---|---|"]
    for a, b in d["地点間"]:
        km, br = pair(pts[a], pts[b])
        out.append(f"| {a} | {b} | {dir16(br)} | 約{km_str(km)}km |")
    out.append("")
    (DIR / "位置台帳.md").write_text("\n".join(out), encoding="utf-8")


def write_svg(d):
    W, H, CY = 2300, 960, 500
    # (題, 中心x, 半径px, 半径km, ラベルを付ける最小km, 対象の群, 目盛り)
    panels = [("広域（半径110km）", 440, 390, 110, 0, ["集落", "標塔", "遠方"], [25, 50, 75, 100]),
              ("近場（半径12km）", 1300, 250, 12, 3.5, ["近場"], [3, 6, 9, 12]),
              ("拠点まわり（半径3.5km）", 1960, 250, 3.5, 0, ["近場"], [1, 2, 3])]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="sans-serif">',
         f'<rect width="{W}" height="{H}" fill="#fbfaf6"/>']
    colors = {"集落": "#b5482f", "標塔": "#3b6ea8", "遠方": "#6b5aa0", "近場": "#2f7d55"}
    for title, cx, R, rkm, rmin, groups, rings in panels:
        k = R / rkm
        cy = CY
        s.append(f'<text x="{cx}" y="40" font-size="22" text-anchor="middle" fill="#333">{title}・北が上・縮尺どおり</text>')
        for rr in rings:
            s.append(f'<circle cx="{cx}" cy="{cy}" r="{rr * k:.1f}" fill="none" stroke="#ccc" stroke-dasharray="4 4"/>')
            s.append(f'<text x="{cx + 4}" y="{cy - rr * k - 4:.1f}" font-size="12" fill="#999">{rr}km</text>')
        s.append(f'<line x1="{cx}" y1="{cy - R - 10}" x2="{cx}" y2="{cy + R + 10}" stroke="#e2e2e2"/>')
        s.append(f'<line x1="{cx - R - 10}" y1="{cy}" x2="{cx + R + 10}" y2="{cy}" stroke="#e2e2e2"/>')
        s.append(f'<text x="{cx}" y="{cy - R - 16}" font-size="16" text-anchor="middle" fill="#666">北</text>')
        if "標塔" in groups:
            # 六角形の辺（隣り合う標塔を結ぶ線）と、図記号
            side = d["格子"]["辺_km"]
            ps = d["標塔"]
            for i, a in enumerate(ps):
                for b in ps[i + 1:]:
                    if abs(math.dist((a["x"], a["y"]), (b["x"], b["y"])) - side) < 0.5:
                        s.append(f'<line x1="{cx + a["x"] * k:.1f}" y1="{cy - a["y"] * k:.1f}" '
                                 f'x2="{cx + b["x"] * k:.1f}" y2="{cy - b["y"] * k:.1f}" '
                                 'stroke="#9cc3a4" stroke-dasharray="5 4"/>')
            for p in ps:
                px, py = cx + p["x"] * k, cy - p["y"] * k
                s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="#888"/>')
                if not p["名"] or p["名"] == f"標塔{p['記号']}":
                    s.append(f'<text x="{px - 6:.1f}" y="{py - 7:.1f}" font-size="13" text-anchor="end" '
                             f'fill="#666">{p["記号"]}</text>')
        s.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#222"/>')
        s.append(f'<text x="{cx - 10}" y="{cy + 22}" font-size="15" text-anchor="end" fill="#222">三ツ辻</text>')
        for p in d["地点"]:
            if p["群"] not in groups or p["km"] > rkm or p["名"] == f"標塔{p.get('記号')}":
                continue
            px, py = cx + p["x"] * k, cy - p["y"] * k
            col = colors[p["群"]]
            if p["km"] <= rmin:
                s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.5" fill="{col}" opacity="0.5"/>')
                continue
            s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{col}"/>')
            pos = p.get("ラベル位置") or ("右" if p["x"] >= -0.01 else "左")
            anchor, dx, dy = {"右": ("start", 9, 5), "左": ("end", -9, 5),
                              "上": ("start", 4, -10), "下": ("start", 4, 20)}[pos]
            s.append(f'<text x="{px + dx:.1f}" y="{py + dy:.1f}" font-size="14" text-anchor="{anchor}" '
                     f'fill="{col}">{(p["記号"] + " ") if p.get("記号") else ""}{p["名"]} {km_str(p["km"])}km</text>')
    s.append("</svg>")
    (DIR / "位置地図.svg").write_text("\n".join(s), encoding="utf-8")


def main():
    d = load()
    names = [p["名"] for p in d["地点"]]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        sys.exit(f"地点名が重複しています: {dup}")
    for p in d["地点"]:
        if p["地形"] not in d["速度"]:
            sys.exit(f"未定義の地形: {p['名']} {p['地形']}")
        # 名前に方角を含む地点は、名前の方角と実際の方角の差が22.5度以内か確かめる
        for w in sorted(DIRS16, key=len, reverse=True):
            if p["名"].startswith(w + "の"):
                diff = abs((DIRS16.index(w) * 22.5 - p["方位"] + 180) % 360 - 180)
                if diff > 22.5:
                    sys.exit(f"名前と方角が不一致: {p['名']} は {dir16(p['方位'])}（{p['方位']:.0f}°）")
                break
        # 入っているべき六角形が指定されていれば確かめる
        if p.get("六角形") and hex_of(d, p["x"], p["y"]) != p["六角形"]:
            sys.exit(f"六角形が不一致: {p['名']} は {hex_of(d, p['x'], p['y'])}（指定: {p['六角形']}）")
    write_md(d)
    write_svg(d)
    print("位置台帳.md と 位置地図.svg を更新しました")


if __name__ == "__main__":
    main()
