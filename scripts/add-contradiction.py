#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ヤヒロ世界設定：新規矛盾の記録ツール
見つかった矛盾を 99_矛盾・未解決事項リスト.md に追加します
"""

import sys
import re
from pathlib import Path
from datetime import datetime

def add_contradiction(code, title, file_a, detail_a, file_b, detail_b, note=""):
    """
    新規矛盾を追加
    code: M999 形式の矛盾コード
    title: 矛盾の タイトル
    file_a, file_b: ファイル名
    detail_a, detail_b: 記述内容
    note: 対処方針など
    """
    contradiction_file = Path(__file__).parent.parent / "設定ドキュメント" / "99_矛盾・未解決事項リスト.md"

    if not contradiction_file.exists():
        print("矛盾リストが見つかりません")
        return False

    with open(contradiction_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 新しい矛盾エントリを作成
    new_entry = f"""### {code}: {title}

- **ファイルA({file_a})**：
  {detail_a}
- **ファイルB({file_b})**：
  {detail_b}
- **要確認**：{note if note else "詳細未定"}
- **対処**：要確認
"""

    # 矛盾セクションの最後に追加
    m_section_end = content.find("## 曖昧・未定義")
    if m_section_end == -1:
        print("矛盾セクションが見つかりません")
        return False

    # 既存のM矛盾の最後を見つける
    existing_m = re.findall(r'### (M\d{3})', content[:m_section_end])
    if existing_m:
        last_m = existing_m[-1]
        # 最後のM矛盾のセクション終了位置を見つける
        last_m_pos = content.rfind(last_m, 0, m_section_end)
        next_section = content.find("\n###", last_m_pos + 1)
        if next_section == -1 or next_section > m_section_end:
            next_section = m_section_end

        content = content[:next_section] + "\n\n" + new_entry + content[next_section:]
    else:
        content = content[:m_section_end] + new_entry + "\n" + content[m_section_end:]

    # 最終更新日時を更新
    content = re.sub(
        r'最終更新：\d{4}-\d{2}-\d{2}',
        f'最終更新：{datetime.now().strftime("%Y-%m-%d")}',
        content
    )

    with open(contradiction_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 矛盾 {code} を追加しました: {title}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python add-contradiction.py <code> <title> [file_a] [detail_a] [file_b] [detail_b]")
        print("例: python add-contradiction.py M008 '新しい矛盾' 'ファイルA.md' '記述内容A' 'ファイルB.md' '記述内容B'")
        sys.exit(1)

    code = sys.argv[1]
    title = sys.argv[2]
    file_a = sys.argv[3] if len(sys.argv) > 3 else "未指定"
    detail_a = sys.argv[4] if len(sys.argv) > 4 else "未記述"
    file_b = sys.argv[5] if len(sys.argv) > 5 else "未指定"
    detail_b = sys.argv[6] if len(sys.argv) > 6 else "未記述"

    add_contradiction(code, title, file_a, detail_a, file_b, detail_b)
