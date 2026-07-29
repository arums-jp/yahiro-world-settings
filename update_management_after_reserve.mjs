import fs from 'node:fs';

const path = '辺境拠点日誌/投稿制御/投稿管理.md';
const today = '2026-06-21';
const reservedIds = new Map([
  [31, 29571899],
  [32, 29571901],
  [33, 29571902],
  [34, 29571904],
  [35, 29571905],
  [36, 29571906],
  [37, 29571907],
  [38, 29571913],
  [39, 29571916],
  [40, 29571922],
  [41, 29571936],
  [42, 29571938],
  [43, 29571942],
  [44, 29571948],
  [45, 29571951],
  [46, 29571956],
  [47, 29571964],
  [48, 29571971],
  [49, 29571979],
  [50, 29571982],
  [51, 29571984],
  [52, 29571985],
  [53, 29571987],
  [54, 29571988],
  [55, 29571990],
  [56, 29571996],
  [57, 29572001],
  [58, 29572003],
  [59, 29572007],
  [60, 29572008],
]);

function pad(number) {
  return String(number).padStart(2, '0');
}

function scheduleForEpisode(episode) {
  const date = new Date(Date.UTC(2026, 5, 23));
  let slots = episode - 31;
  while (slots > 0) {
    date.setUTCDate(date.getUTCDate() + 1);
    const day = date.getUTCDay();
    if (day === 2 || day === 4 || day === 6) slots -= 1;
  }
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())} 20:10 JST`;
}

function splitMarkdownRow(line) {
  return line
    .trim()
    .slice(1, -1)
    .split('|')
    .map((cell) => cell.trim());
}

function makeRow(cells) {
  return `| ${cells.join(' | ')} |`;
}

let content = fs.readFileSync(path, 'utf8');
content = content
  .replace('- 投稿準備状況：第1〜30話 公開済み / 第31〜71話 下書き保存済み', '- 投稿準備状況：第1〜30話 公開済み / 第31〜60話 予約設定済み / 第61〜71話 下書き保存済み')
  .replace('- 公開状況：第1〜30話 公開済み、第31〜71話 未投稿・未計画', '- 公開状況：第1〜30話 公開済み、第31〜60話 予約済み、第61〜71話 未投稿（予約上限到達のため未設定）');

const lines = content.split(/\r?\n/).map((line) => {
  if (!line.startsWith('| 第')) return line;
  const cells = splitMarkdownRow(line);
  const episode = Number(cells[2].replace(/,/g, ''));
  if (!Number.isFinite(episode)) return line;

  if (reservedIds.has(episode)) {
    const id = reservedIds.get(episode);
    cells[5] = '予約設定済み';
    cells[6] = String(id);
    cells[7] = `[詳細](https://syosetu.com/usernoveldatamanage/top/ncode/3145031/noveldataid/${id}/)`;
    cells[8] = today;
    cells[9] = scheduleForEpisode(episode);
    cells[10] = '予約設定済み';
    cells[11] = today;
    cells[12] = '予約済み';
    cells[13] = `予約設定: ${today}`;
    return makeRow(cells);
  }

  if (episode >= 61 && episode <= 71) {
    cells[5] = '下書き保存済み';
    cells[8] = today;
    cells[9] = scheduleForEpisode(episode);
    cells[10] = '予約予定';
    cells[11] = '';
    cells[12] = '未投稿';
    cells[13] = `下書き状態確認: ${today} / 予約上限到達のため未設定`;
    return makeRow(cells);
  }

  return line;
});

fs.writeFileSync(path, `${lines.join('\n')}\n`, 'utf8');
