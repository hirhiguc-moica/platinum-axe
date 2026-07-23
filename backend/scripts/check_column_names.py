"""モデルとスクリプトのカラム名不一致をチェック"""

import re
from pathlib import Path

# モデルファイルからカラム名抽出
model_file = Path(__file__).parent.parent / "app/domain/models/technical_indicator.py"
with open(model_file) as f:
    model_content = f.read()

# Mapped[...]のパターンでカラム抽出
model_columns = set()
for match in re.finditer(r"^\s+([a-z_0-9]+):\s+Mapped\[", model_content, re.MULTILINE):
    col = match.group(1)
    if col not in ["stock_code", "date", "calculated_at"]:  # メタカラムを除外
        model_columns.add(col)

print(f"モデルのテクニカル指標カラム数: {len(model_columns)}")

# スクリプトファイルからカラム名抽出
script_file = Path(__file__).parent / "seed_stock_prices.py"
with open(script_file) as f:
    script_content = f.read()

# result["カラム名"] = ... のパターンでカラム抽出
script_columns = set()
for match in re.finditer(r'result\["([a-z_0-9]+)"\]', script_content):
    col = match.group(1)
    if col not in ["date"]:  # メタカラムを除外
        script_columns.add(col)

print(f"スクリプトのテクニカル指標カラム数: {len(script_columns)}")

# 不一致を検出
model_only = model_columns - script_columns
script_only = script_columns - model_columns

print(f"\n{'=' * 60}")
print("不一致レポート")
print(f"{'=' * 60}\n")

if model_only:
    print(f"❌ モデルにあるがスクリプトにない（{len(model_only)}個）:")
    for col in sorted(model_only):
        print(f"  - {col}")
else:
    print("✅ モデルにあるがスクリプトにない: なし")

print()

if script_only:
    print(f"❌ スクリプトにあるがモデルにない（{len(script_only)}個）:")
    for col in sorted(script_only):
        print(f"  - {col}")
else:
    print("✅ スクリプトにあるがモデルにない: なし")

print()

if not model_only and not script_only:
    print("✅ すべてのカラム名が一致しています！")
else:
    print(f"⚠️  合計 {len(model_only) + len(script_only)} 個の不一致があります")

# 推測される対応関係を表示
print(f"\n{'=' * 60}")
print("推測される対応関係")
print(f"{'=' * 60}\n")

# 類似カラム名を検出（末尾に数字がある/ない等）
potential_matches = []
for s_col in sorted(script_only):
    for m_col in sorted(model_only):
        # パターン1: スクリプト側に数字なし、モデル側に数字あり
        if m_col.startswith(s_col + "_"):
            potential_matches.append((s_col, m_col))
        # パターン2: 部分一致
        elif s_col in m_col or m_col in s_col:
            potential_matches.append((s_col, m_col))

if potential_matches:
    for s_col, m_col in potential_matches:
        print(f"  {s_col} → {m_col}")
else:
    print("  推測できる対応関係はありません")
