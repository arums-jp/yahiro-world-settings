#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ヤヒロ世界設定の整合性チェックツール
矛盾・曖昧点・数値パラメータの一貫性を検証します
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict

# Windows環境での出力エンコーディング設定
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class YahiroConsistencyChecker:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.doc_dir = self.base_dir / "設定ドキュメント"
        self.files = {}
        self.contradictions = []
        self.load_files()

    def load_files(self):
        """設定ファイルを読み込む"""
        for i in range(1, 9):
            filename = f"{i:02d}_*.md"
            matches = list(self.doc_dir.glob(filename))
            if matches:
                filepath = matches[0]
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.files[filepath.name] = f.read()

    def find_values(self, keyword):
        """キーワードに関連する値を全ファイルから抽出"""
        results = {}
        pattern = re.compile(rf'{keyword}[：:]?\s*（?([^）\n]+?)(?:）|$|\n)', re.IGNORECASE)

        for filename, content in self.files.items():
            matches = pattern.findall(content)
            if matches:
                results[filename] = matches
        return results

    def check_radius_values(self):
        """ヤヒロの半径・外殻値をチェック"""
        print("【数値パラメータチェック】\n")

        params = [
            ("外殻半径", "Yahiro external radius"),
            ("地表半径", "Surface radius"),
            ("人工太陽軌道", "Artificial sun orbit"),
            ("第2層", "Layer 2 radius"),
            ("第4層", "Layer 4 radius"),
            ("第5層", "Layer 5 radius"),
            ("MTM残存", "MTM remaining"),
        ]

        for jp_param, en_param in params:
            results = self.find_values(jp_param)
            if len(results) > 1:
                print(f"[!] {jp_param}:")
                for filename, values in results.items():
                    print(f"  - {filename}: {', '.join(values[:2])}")
                print()

    def check_contradiction_list(self):
        """矛盾リストを読み込んで要確認状況を表示"""
        contradiction_file = self.doc_dir / "99_矛盾・未解決事項リスト.md"
        if not contradiction_file.exists():
            print("【矛盾リスト】見つかりません\n")
            return

        with open(contradiction_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # M（矛盾）セクションを抽出
        m_section = re.search(r'## 矛盾・食い違い(.*?)## 曖昧', content, re.DOTALL)
        if m_section:
            contradictions = re.findall(r'### (M\d{3}):?\s*([^\n]+)', m_section.group(1))
            print(f"【矛盾リスト（M）】 {len(contradictions)}件\n")
            for code, title in contradictions[:7]:
                print(f"  {code}: {title}")
            print()

        # U（曖昧）セクションを抽出
        u_section = re.search(r'## 曖昧・未定義(.*?)## 独自単位', content, re.DOTALL)
        if u_section:
            ambiguities = re.findall(r'### (U\d{3}):?\s*([^\n]+)', u_section.group(1))
            print(f"【曖昧・未定義（U）】 {len(ambiguities)}件\n")
            for code, title in ambiguities[:8]:
                print(f"  {code}: {title}")
            print()

    def find_要確認_markers(self):
        """全ファイルから「※要確認」マーカーを検索"""
        print("【要確認マーカー検索】\n")
        total_markers = 0

        for filename, content in self.files.items():
            markers = re.findall(r'[^\n]*※要確認[^\n]*', content)
            if markers:
                print(f"[*] {filename}: {len(markers)}件")
                for marker in markers[:2]:
                    truncated = marker[:60] + "..." if len(marker) > 60 else marker
                    print(f"  - {truncated}")
                if len(markers) > 2:
                    print(f"  ... ほか {len(markers)-2}件")
                total_markers += len(markers)

        if total_markers == 0:
            print("[OK] 要確認マーカーはありません")
        print()

    def run_all_checks(self):
        """全チェックを実行"""
        print("=" * 60)
        print("ヤヒロ世界設定 整合性チェック")
        print("=" * 60)
        print()

        print(f"[*] 読み込みファイル: {len(self.files)}個\n")

        self.check_contradiction_list()
        self.check_radius_values()
        self.find_要確認_markers()

        print("=" * 60)
        print("[OK] チェック完了")
        print("=" * 60)

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    checker = YahiroConsistencyChecker(base_dir)
    checker.run_all_checks()
