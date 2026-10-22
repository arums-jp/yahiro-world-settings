"""Generate an editable schematic SVG and a matching PNG for the comedy edition."""
from pathlib import Path
from html import escape
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '辺境拠点日誌_コメディ強化版' / '設定'
OUT.mkdir(exist_ok=True)
W, H = 1800, 1500
BG, INK, MUTED = '#faf8f2', '#243b45', '#63767c'
BLUE, GREEN, RED, GOLD = '#538caa', '#769676', '#b54f46', '#b58a48'
im = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(im)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<title>三ツ辻を中心とした周辺地図・コメディ強化版</title>',
       '<desc>広域図と近傍拡大図。縮尺なし。移動時間は全て拠点から片道。</desc>',
       f'<rect width="{W}" height="{H}" fill="{BG}"/>']

def text(x, y, s, size=24, color=INK, bold=False):
    font = ImageFont.truetype('C:/Windows/Fonts/meiryob.ttc' if bold else 'C:/Windows/Fonts/meiryo.ttc', size)
    d.text((x, y), s, font=font, fill=color, anchor='lt')
    svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" font-family="Meiryo, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(s)}</text>')

def box(x, y, w, h, fill='#ffffff', stroke='#dedfd6', radius=16):
    d.rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=fill, outline=stroke, width=2)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')

def line(points, color=MUTED, width=3, dashed=False):
    if dashed:
        for a, b in zip(points, points[1:]):
            length = math.dist(a,b)
            for t in range(0, int(length), 16):
                e = min(t+8,length)
                d.line([(a[0]+(b[0]-a[0])*v/length,a[1]+(b[1]-a[1])*v/length) for v in (t,e)], fill=color, width=width)
    else:
        d.line(points, fill=color, width=width, joint='curve')
    coords=' '.join(f'{x},{y}' for x,y in points)
    dash=' stroke-dasharray="8 8"' if dashed else ''
    svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{dash}/>')

def dot(x,y,color=INK,r=8):
    d.ellipse((x-r,y-r,x+r,y+r), fill=color)
    svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

def polygon(points, fill):
    d.polygon(points,fill=fill)
    svg.append(f'<polygon points="'+ ' '.join(f'{x},{y}' for x,y in points)+f'" fill="{fill}"/>')

text(45,32,'三ツ辻を中心とした周辺地図',42,bold=True)
text(47,94,'コメディ強化版・執筆参照用  ｜  移動時間はすべて拠点から片道  ｜  2026-10-23',23,color=MUTED)
box(40,150,1040,880)
box(1110,150,650,880)
text(68,172,'01  広域図',29,bold=True)
text(68,218,'三集落と六本の標塔／参考画像の相対配置を踏襲',21,color=MUTED)
text(1140,172,'02  拠点近傍・拡大図',29,bold=True)
text(1140,218,'近場の目的地と遠方の標塔を区別する',21,color=MUTED)

# The reference image's A–F marks identify positions, not in-world tower names.
nodes={'A':(490,350),'C':(760,350),'D':(875,555),'B':(760,760),'E':(490,760),'F':(375,555)}
line([nodes[k] for k in ['A','C','D','B','E','F','A']],GREEN,2,True)
c=(560,565)
for pts in [[c,(410,400),(290,285)],[c,(740,730),(930,900)],[c,(360,735),(185,895)]]:
    line(pts,GOLD,5)

# Approximate landscape bands. These are symbols, not surveyed boundaries.
line([(330,640),(350,690),(320,740),(305,790),(270,845)],BLUE,6)
text(84,730,'ナル川',23,color=BLUE)
polygon([(350,720),(385,690),(445,730),(430,835),(320,875),(290,825)],'#edf1e7')
text(335,882,'森の縁ルート',21,color=GREEN)
text(155,410,'丘陵越え',21,color=MUTED)
text(845,810,'川沿い',21,color=MUTED)

for k,(x,y) in nodes.items():
    dot(x,y,GREEN,8)
labels=[('A',415,275,'北の標塔','約37km'),('C',726,275,'北東の標塔','約44km'),
        ('D',895,510,'東の標塔','約45km'),('B',745,675,'南東の標塔','約40km'),
        ('E',435,795,'南南西の標塔','約33km'),('F',90,520,'西南西の標塔','約31km')]
for k,x,y,name,dist in labels:
    text(x,y,f'{k}  {name}',23,bold=True)
    text(x,y+34,dist+'／徒歩2日',21,color=MUTED)

dot(*c,RED,13)
box(440,588,250,90,'#fff3ed','#e7c7b8')
text(480,600,'三ツ辻拠点',30,color=RED,bold=True)
text(478,644,'すべての移動の起点',20,color=MUTED)

for x,y,tx,ty,name,dist,days in [
    (290,285,70,275,'カネヅカ','北西・約55km','徒歩3.5〜4日'),
    (930,900,790,920,'ミナシロ','南東・約60km','徒歩4〜5日'),
    (185,895,70,925,'ハラダ','南西・約70km','徒歩4.5〜5日')]:
    dot(x,y,BLUE,11)
    text(tx,ty,name,28,color=INK,bold=True)
    text(tx,ty+40,dist,22,color=MUTED)
    text(tx,ty+73,days,22,color=INK)

# A compact north arrow, outside the labelled locations.
line([(1010,370),(1010,290)],INK,3)
polygon([(1010,280),(1001,300),(1019,300)],INK)
text(994,250,'北',23,bold=True)

# Local inset; distances are labelled rather than derived from page geometry.
line([(1210,278),(1190,370),(1215,445),(1190,530),(1215,640),(1185,715)],BLUE,9)
text(1245,292,'ナル川',23,color=BLUE,bold=True)
text(1245,326,'西・徒歩15分',20,color=MUTED)
local=(1450,465)
line([local,(1300,465),(1210,465)],GOLD,4)
line([(1200,451),(1225,451)],INK,3)
line([(1200,478),(1225,478)],INK,3)
text(1140,505,'渡河地点・橋',21,color=BLUE)
line([local,(1540,325)],GOLD,4)
dot(1540,325,MUTED,9)
text(1470,263,'大岩',26,bold=True)
text(1470,300,'北東・徒歩20分',21,color=MUTED)
line([local,(1625,465)],GOLD,4)
line([(1625,465),(1690,410)],GOLD,3)
line([(1625,465),(1700,520)],GOLD,3)
line([(1625,465),(1570,550)],GOLD,3)
dot(1625,465,GOLD,8)
text(1550,560,'三叉路',25,bold=True)
text(1530,598,'東寄り・徒歩5分',21,color=MUTED)
dot(*local,RED,12)
text(1370,494,'三ツ辻拠点',27,color=RED,bold=True)
line([local,(1450,665)],GOLD,4)
dot(1450,665,GREEN,9)
text(1475,650,'B-7 石柱',25,bold=True)
text(1475,689,'南・徒歩30分',21,color=MUTED)

polygon([(1150,780),(1230,690),(1320,715),(1400,810),(1370,970),(1150,970)],'#edf1e7')
line([local,(1335,675),(1270,790),(1280,915)],GOLD,4)
text(1140,745,'暗い森の入口',24,color=GREEN,bold=True)
text(1140,784,'南西・徒歩約1時間',21,color=MUTED)
text(1140,836,'針鼠狼の出没域',20,color=GREEN)
dot(1280,915,RED,9)
text(1320,875,'禁域の入口',25,color=RED,bold=True)
text(1320,914,'南南西・徒歩約3時間',21)
text(1320,950,'標塔33kmよりずっと手前',19,color=MUTED)

# Supporting destinations: avoid invented precise bearings and distances.
box(40,1055,1040,250)
text(68,1076,'03  道中の目的地',28,bold=True)
text(68,1126,'廃坑',25,bold=True)
text(255,1126,'カネヅカ道の途中で北へ分岐',24)
text(255,1162,'徒歩3日（野営2泊）／馬で約1.5日',23,color=MUTED)
text(68,1211,'ミナシロ出作り地',24,bold=True)
text(365,1211,'南東・約10km／徒歩2〜3時間',23)
text(365,1249,'霧の窪地・B-6・被害の畑／本村とは別',21,color=MUTED)
box(1110,1055,650,250)
text(1140,1076,'04  位置を固定しない地点',28,bold=True)
text(1140,1126,'B-12・B-15',24,bold=True)
text(1140,1165,'拠点から徒歩1〜2時間圏／方角は未確定',21,color=MUTED)
text(1140,1210,'外部市',24,bold=True)
text(1280,1210,'北西側／徒歩片道5日',22)
text(1140,1250,'倒れた標塔：北西遠征先／位置・距離は要確認',20,color=MUTED)

dot(57,1350,RED,7)
text(75,1336,'拠点',23,color=MUTED)
dot(167,1350,BLUE,7)
text(185,1336,'集落',23,color=MUTED)
dot(277,1350,GREEN,7)
text(295,1336,'標塔・石柱',23,color=MUTED)
text(495,1336,'━ 主要道（模式）    ┄ 参考図の補助線',23,color=MUTED)
text(45,1380,'縮尺なし。図上の間隔ではなく、記載した距離・所要時間を参照。標塔のA〜Fは参考画像との対応記号。',22)
text(45,1419,'徒歩日数は設定資料の通常目安。危険回避・迂回は別途1〜2日。往復は原則2倍＋現地作業・滞在日数。',22)
text(45,1458,'出典：三ツ辻拠点2.png／拠点と周辺地理.md／コメディ強化版 第88・120〜126話。配置・経路線は模式表現。',19,color=MUTED)
svg.append('</svg>')
stem=OUT/'三ツ辻中心_移動参照地図'
stem.with_suffix('.svg').write_text('\n'.join(svg),encoding='utf-8')
im.save(stem.with_suffix('.png'))
print(stem.with_suffix('.png'))
print(stem.with_suffix('.svg'))
