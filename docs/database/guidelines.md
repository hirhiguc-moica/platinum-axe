# データベース設計ガイドライン

**最終更新**: 2026-07-21

---

## 基本方針

### 1. トランザクションデータ保存

**原則**: APIから取得したデータは、全て生データとして保存する

**理由**:
- データの履歴追跡が可能
- バグ修正時に過去データの再処理ができる
- データ品質チェック・監査が容易

**例**:
```sql
-- J-Quants APIから取得した株価データは全て保存
INSERT INTO stock_prices_daily (stock_code, date, open, high, low, close, volume, fetched_at)
VALUES ('7203', '2026-07-21', 2500, 2550, 2480, 2530, 1000000, NOW());
```

### 2. 計算済みデータの事前保存

**原則**: テクニカル指標等の計算結果はDBに保存する

**理由**:
- 推論時の計算コストを削減
- 毎回計算するとパフォーマンスが悪化
- バッチ処理で一括計算できる

**例**:
```sql
-- 移動平均等のテクニカル指標を事前計算して保存
INSERT INTO technical_indicators (stock_code, date, sma_5, sma_20, rsi_14)
VALUES ('7203', '2026-07-21', 2520, 2480, 55.5);
```

### 3. 特徴量ストア

**原則**: 機械学習用の特徴量は、JSONB形式で柔軟に保存

**理由**:
- 特徴量の追加・削除が容易
- スキーマ変更が不要
- 後から特徴量を追加しても過去データを再処理可能

**例**:
```sql
-- 全特徴量をJSONB形式で保存
INSERT INTO ml_features (stock_code, date, features)
VALUES ('7203', '2026-07-21', '{
  "fundamental": {"per": 15.5, "pbr": 1.2, "roe": 8.5},
  "technical": {"sma_5": 2520, "rsi_14": 55.5},
  "sentiment": {"margin_ratio": 1.5}
}'::jsonb);
```

---

## 命名規則

### テーブル名

- **小文字 + アンダースコア**: `stock_prices_daily`
- **複数形**: `recommendations`（単数形 `recommendation`ではない）
- **説明的な名前**: 略語は避ける

### カラム名

- **小文字 + アンダースコア**: `stock_code`, `created_at`
- **主キー**: `id`（`{table_name}_id`ではない）
- **外部キー**: `{参照テーブル}_id`（例: `round_id`）
- **日付**: `{意味}_date`（例: `start_date`, `end_date`）
- **タイムスタンプ**: `{意味}_at`（例: `created_at`, `fetched_at`）

### インデックス名

- **プレフィックス**: `idx_{table_name}_{column_name}`
- **ユニーク制約**: `uq_{table_name}_{column_name}`
- **外部キー制約**: `fk_{table_name}_{column_name}`

**例**:
```sql
-- インデックス
CREATE INDEX idx_stock_prices_daily_stock_code_date ON stock_prices_daily(stock_code, date);

-- ユニーク制約
ALTER TABLE stock_master ADD CONSTRAINT uq_stock_master_stock_code UNIQUE(stock_code);

-- 外部キー制約
ALTER TABLE round_recommendations
ADD CONSTRAINT fk_round_recommendations_round_id
FOREIGN KEY (round_id) REFERENCES rounds(id);
```

---

## データ型ガイドライン

### 数値型

| 用途 | データ型 | 例 |
|------|---------|---|
| 主キー | `BIGSERIAL` | `id BIGSERIAL PRIMARY KEY` |
| 整数 | `INTEGER` | `volume INTEGER` |
| 大きな整数 | `BIGINT` | `volume BIGINT`（出来高等） |
| 金額・価格 | `DECIMAL(10,2)` | `close DECIMAL(10,2)` |
| 比率・率 | `DECIMAL(8,4)` | `per DECIMAL(8,4)` |
| パーセント | `DECIMAL(6,3)` | `growth_rate DECIMAL(6,3)`（-99.999 〜 999.999） |

### 文字列型

| 用途 | データ型 | 例 |
|------|---------|---|
| 銘柄コード | `VARCHAR(10)` | `stock_code VARCHAR(10)` |
| 銘柄名 | `VARCHAR(255)` | `stock_name VARCHAR(255)` |
| Enum（短い） | `VARCHAR(20)` | `round_type VARCHAR(20)` |
| テキスト | `TEXT` | `description TEXT` |
| JSON | `JSONB` | `features JSONB` |

### 日付・時刻型

| 用途 | データ型 | 例 |
|------|---------|---|
| 日付のみ | `DATE` | `date DATE` |
| タイムスタンプ | `TIMESTAMP` | `created_at TIMESTAMP DEFAULT NOW()` |
| タイムゾーン付き | `TIMESTAMPTZ` | `fetched_at TIMESTAMPTZ` |

### 真偽値型

| 用途 | データ型 | 例 |
|------|---------|---|
| フラグ | `BOOLEAN` | `is_active BOOLEAN DEFAULT TRUE` |

---

## NULL制約

### NOT NULL を設定すべきカラム

- 主キー（自動設定）
- 外部キー
- 必須の業務データ（銘柄コード、日付等）
- タイムスタンプ（`created_at`, `updated_at`）

### NULL を許容すべきカラム

- オプショナルな情報（配当利回り等）
- データ取得失敗時にNULLになる可能性があるもの
- 後から追加される情報

**例**:
```sql
CREATE TABLE stock_prices_daily (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,        -- 必須
    date DATE NOT NULL,                     -- 必須
    open DECIMAL(10,2),                     -- オプショナル（取得失敗時NULL）
    close DECIMAL(10,2) NOT NULL,           -- 必須（終値は必ず存在）
    fetched_at TIMESTAMP NOT NULL,          -- 必須
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## インデックス戦略

### インデックスを設定すべきカラム

1. **主キー**: 自動的にインデックスが作成される
2. **外部キー**: クエリの高速化のため
3. **頻繁に検索されるカラム**: `stock_code`, `date`
4. **UNIQUE制約付きカラム**: 一意性保証のため
5. **ORDER BY / GROUP BYで使われるカラム**

### 複合インデックス

**原則**: クエリのWHERE句に複数カラムが登場する場合、複合インデックスを作成

**カラムの順序**: 選択性の高いカラムを先頭に

**例**:
```sql
-- stock_code, dateの順で検索されることが多い
CREATE INDEX idx_stock_prices_daily_stock_code_date
ON stock_prices_daily(stock_code, date);

-- このクエリは高速化される
SELECT * FROM stock_prices_daily
WHERE stock_code = '7203' AND date >= '2026-01-01';
```

### 部分インデックス

**原則**: 特定の条件のレコードのみをインデックス化

**例**:
```sql
-- アクティブなラウンドのみインデックス化
CREATE INDEX idx_rounds_active
ON rounds(start_date)
WHERE status = 'ACTIVE';
```

---

## 制約設計

### UNIQUE制約

**原則**: 業務上一意であるべきカラムにはUNIQUE制約を設定

**例**:
```sql
-- 銘柄コード + 日付の組み合わせは一意
ALTER TABLE stock_prices_daily
ADD CONSTRAINT uq_stock_prices_daily_stock_code_date
UNIQUE(stock_code, date);
```

### CHECK制約

**原則**: 値の範囲を制限する

**例**:
```sql
-- 予測騰落率は-100%〜+1000%の範囲
ALTER TABLE round_recommendations
ADD CONSTRAINT chk_round_recommendations_predicted_return
CHECK (predicted_return >= -100 AND predicted_return <= 1000);

-- 信頼度スコアは0〜100の範囲
ALTER TABLE round_recommendations
ADD CONSTRAINT chk_round_recommendations_confidence_score
CHECK (confidence_score >= 0 AND confidence_score <= 100);
```

### 外部キー制約

**原則**: 参照整合性を保証する

**ON DELETE**: 親レコード削除時の挙動を定義

| 動作 | 説明 | 使用例 |
|------|------|--------|
| `CASCADE` | 親削除時に子も削除 | ラウンド削除時に推奨銘柄も削除 |
| `SET NULL` | 親削除時に子をNULL | あまり使わない |
| `RESTRICT` | 子が存在する場合は削除不可 | デフォルト |

**例**:
```sql
-- ラウンド削除時に推奨銘柄も削除
ALTER TABLE round_recommendations
ADD CONSTRAINT fk_round_recommendations_round_id
FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE;
```

---

## タイムスタンプ管理

### 標準パターン

全テーブルに以下のカラムを追加:

```sql
CREATE TABLE example (
    id BIGSERIAL PRIMARY KEY,
    -- ... 業務カラム ...
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 更新日時の自動更新

**Alembicマイグレーション**で以下を実行:

```python
# Trigger関数を作成
op.execute("""
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

# Triggerを設定
op.execute("""
CREATE TRIGGER update_example_updated_at
BEFORE UPDATE ON example
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
""")
```

---

## JSONBの使い方

### 特徴量ストアでの使用

**メリット**:
- スキーマ変更不要
- 柔軟な構造
- PostgreSQLのJSONB演算子で高速検索

**例**:
```sql
-- 特徴量をJSONB形式で保存
INSERT INTO ml_features (stock_code, date, features)
VALUES ('7203', '2026-07-21', '{
  "fundamental": {
    "per": 15.5,
    "pbr": 1.2,
    "roe": 8.5
  },
  "technical": {
    "sma_5": 2520,
    "sma_20": 2480,
    "rsi_14": 55.5
  }
}'::jsonb);

-- JSONB演算子での検索
SELECT * FROM ml_features
WHERE features->'fundamental'->>'per' > '15';

-- インデックス作成
CREATE INDEX idx_ml_features_fundamental_per
ON ml_features((features->'fundamental'->>'per'));
```

---

## パーティショニング

### 将来的な最適化（MVP段階では不要）

データ量が増えた場合、日付によるパーティショニングを検討:

```sql
-- 年月によるパーティショニング（例）
CREATE TABLE stock_prices_daily (
    id BIGSERIAL,
    stock_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    -- ...
) PARTITION BY RANGE (date);

-- 2026年1月のパーティション
CREATE TABLE stock_prices_daily_202601
PARTITION OF stock_prices_daily
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## マイグレーション戦略

### Alembic使用

**原則**: 全てのスキーマ変更はAlembicマイグレーションで管理

**推奨フロー**:

```bash
# 1. モデル変更
vim backend/app/infrastructure/database/models.py

# 2. マイグレーションファイル自動生成
cd backend
uv run alembic revision --autogenerate -m "Add new column to stock_master"

# 3. マイグレーションファイルを確認・修正
vim alembic/versions/xxxx_add_new_column_to_stock_master.py

# 4. マイグレーション適用
uv run alembic upgrade head
```

### データシード

**原則**: マイグレーションファイル内でシードデータを投入

**例**:
```python
from alembic import op

def upgrade():
    # テーブル作成
    op.create_table('stock_master', ...)

    # シードデータ投入
    op.execute("""
        INSERT INTO stock_master (stock_code, stock_name, sector)
        VALUES ('7203', 'トヨタ自動車', '輸送用機器');
    """)

def downgrade():
    op.drop_table('stock_master')
```

---

## パフォーマンスチューニング

### クエリ最適化

1. **EXPLAIN ANALYZE** でクエリプランを確認

```sql
EXPLAIN ANALYZE
SELECT * FROM stock_prices_daily
WHERE stock_code = '7203' AND date >= '2026-01-01';
```

2. **インデックスが使われているか確認**

3. **N+1問題を避ける**: SQLAlchemyの`joinedload()`を使用

### バッチ挿入

**原則**: 大量データは`executemany()`でバッチ挿入

```python
# 悪い例（遅い）
for row in rows:
    session.add(StockPrice(**row))
session.commit()

# 良い例（速い）
session.bulk_insert_mappings(StockPrice, rows)
session.commit()
```

---

## バックアップ戦略

### 開発環境

**手動バックアップ**:

```bash
# ダンプ
pg_dump -h localhost -U platinum platinum_axe > backup.sql

# リストア
psql -h localhost -U platinum platinum_axe < backup.sql
```

### 本番環境（将来）

- GCP Cloud SQLの自動バックアップ機能を使用
- 毎日自動バックアップ
- ポイントインタイムリカバリ有効化

---

## 参考情報

- **PostgreSQL公式ドキュメント**: https://www.postgresql.org/docs/
- **SQLAlchemy公式ドキュメント**: https://docs.sqlalchemy.org/
- **Alembic公式ドキュメント**: https://alembic.sqlalchemy.org/

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
