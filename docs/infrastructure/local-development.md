# ローカル開発環境 - DevContainer構成

**最終更新**: 2026-07-21

---

## 概要

**VSCode DevContainer** を使用した統一開発環境を提供します。

### 利点

- ✅ **環境統一**: 全開発者が同一環境で作業可能
- ✅ **セットアップ不要**: Docker + VSCodeのみで即開発開始
- ✅ **OS非依存**: macOS, Windows, Linuxで動作
- ✅ **依存関係管理**: Python, Node.js, PostgreSQL, Redisを自動構築
- ✅ **VSCode拡張機能**: 必要な拡張機能を自動インストール

---

## 前提条件

### 必須ソフトウェア

以下をインストールしてください:

1. **Docker Desktop**
   - macOS/Windows: [公式サイト](https://www.docker.com/products/docker-desktop/)からダウンロード
   - Linux: Docker Engine + Docker Composeをインストール
   - 最低要件: メモリ4GB以上（推奨: 8GB以上）

2. **Visual Studio Code**
   - [公式サイト](https://code.visualstudio.com/)からダウンロード

3. **VSCode拡張機能: Dev Containers**
   - VSCode拡張機能検索で「Dev Containers」をインストール
   - もしくは: `code --install-extension ms-vscode-remote.remote-containers`

---

## 起動手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/[your-username]/platinum-axe.git
cd platinum-axe
```

### 2. VSCodeでプロジェクトを開く

```bash
code .
```

### 3. DevContainerで再オープン

VSCodeが起動したら、以下のいずれかの方法で:

**方法A: 通知から**
- 右下に表示される通知「Reopen in Container」をクリック

**方法B: コマンドパレットから**
- `Cmd+Shift+P` (macOS) / `Ctrl+Shift+P` (Windows/Linux)
- 「Dev Containers: Reopen in Container」を選択

**方法C: 左下アイコンから**
- 左下の `><` アイコンをクリック
- 「Reopen in Container」を選択

### 4. 初回ビルド（数分かかります）

初回は以下の処理が自動実行されます:

```
【Docker イメージビルド】
├─ Python 3.12インストール
├─ Node.js 22インストール
├─ uvインストール（Pythonパッケージマネージャー）
├─ pnpmインストール（Node.jsパッケージマネージャー）
└─ PostgreSQL 15, Redis 7起動

【VSCode拡張機能インストール】
├─ Python, Pylance, Ruff
├─ ESLint, Prettier
└─ Tailwind CSS, Docker等

【依存関係インストール】
├─ cd /workspace/backend && uv sync --all-extras
└─ cd /workspace/frontend && pnpm install
```

### 5. 起動完了確認

ターミナル（VSCode内）で以下を確認:

```bash
# Python バージョン確認
python --version
# => Python 3.12.x

# Node.js バージョン確認
node --version
# => v22.x.x

# PostgreSQL接続確認
psql -h db -U platinum -d platinum_axe
# => パスワード: platinum
# => psql (15.x) と表示されればOK

# Redis接続確認
redis-cli -h redis ping
# => PONG と表示されればOK
```

---

## ディレクトリ構造

DevContainer内部では、以下のパスでプロジェクトがマウントされます:

```
/workspace/
├── .devcontainer/         # DevContainer設定
│   ├── devcontainer.json  # VSCode設定
│   ├── docker-compose.yml # Dockerサービス定義
│   └── Dockerfile         # appコンテナイメージ
│
├── backend/               # Backendプロジェクト
│   ├── app/               # アプリケーションコード
│   ├── tests/             # テストコード
│   ├── pyproject.toml     # Python依存関係
│   └── .venv/             # 仮想環境（uv管理）
│
├── frontend/              # Frontendプロジェクト
│   ├── app/               # Next.jsアプリケーション
│   ├── package.json       # Node.js依存関係
│   └── node_modules/      # パッケージ（pnpm管理）
│
├── ml/                    # 機械学習プロジェクト
├── batch/                 # バッチ処理
└── docs/                  # ドキュメント
```

---

## サービス構成

DevContainerは以下の3つのコンテナで構成されます:

### 1. app（開発環境）

```yaml
service: app
image: Python 3.12 + Node.js 22
ports:
  - 8000: Backend (FastAPI)
  - 3000: Frontend (Next.js)
volumes:
  - ../:/workspace:cached
```

**インストール済みツール**:
- Python 3.12 + uv
- Node.js 22 + pnpm
- Git, vim, curl
- postgresql-client, redis-tools

### 2. db（PostgreSQL 15）

```yaml
service: db
image: postgres:15-alpine
ports:
  - 5432: PostgreSQL
environment:
  POSTGRES_USER: platinum
  POSTGRES_PASSWORD: platinum
  POSTGRES_DB: platinum_axe
volumes:
  - postgres-data: /var/lib/postgresql/data
```

### 3. redis（Redis 7）

```yaml
service: redis
image: redis:7-alpine
ports:
  - 6379: Redis
volumes:
  - redis-data: /data
```

---

## 環境変数設定

### Backend `.env`ファイル

`backend/.env`を作成し、以下を設定:

```bash
# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://platinum:platinum@db:5432/platinum_axe

# Redis
REDIS_URL=redis://redis:6379/0

# J-Quants API
JQUANTS_REFRESH_TOKEN=your_refresh_token_here
JQUANTS_API_BASE_URL=https://api.jquants.com/v1

# ML Model
ML_MODEL_DIR=/workspace/ml/models
```

**注意**:
- `.env`ファイルは`.gitignore`に登録済み（コミット禁止）
- `.env.example`をコピーして使用してください

### Frontend `.env.local`ファイル（将来的に必要な場合）

`frontend/.env.local`を作成:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 開発サーバー起動

### Backend起動（FastAPI）

ターミナル1で:

```bash
cd /workspace/backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで確認:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend起動（Next.js）

ターミナル2で:

```bash
cd /workspace/frontend
pnpm dev
```

ブラウザで確認:
- Frontend: http://localhost:3000

---

## データベース操作

### Alembicマイグレーション

#### 初期マイグレーション作成

```bash
cd /workspace/backend
uv run alembic revision --autogenerate -m "Initial migration"
```

#### マイグレーション適用

```bash
cd /workspace/backend
uv run alembic upgrade head
```

#### マイグレーション履歴確認

```bash
cd /workspace/backend
uv run alembic history
```

#### マイグレーション巻き戻し

```bash
cd /workspace/backend
uv run alembic downgrade -1
```

### psqlでDB直接操作

```bash
psql -h db -U platinum -d platinum_axe
```

よく使うコマンド:

```sql
-- テーブル一覧
\dt

-- テーブル構造確認
\d stock_master

-- データ確認
SELECT * FROM stock_master LIMIT 10;

-- 終了
\q
```

---

## テスト実行

### Backend テスト

```bash
cd /workspace/backend
uv run pytest
```

**カバレッジ付き**:

```bash
cd /workspace/backend
uv run pytest --cov=app --cov-report=html
```

カバレッジレポート: `backend/htmlcov/index.html`

### Frontend テスト（将来実装予定）

```bash
cd /workspace/frontend
pnpm test
```

---

## コードフォーマット・リンター

### Backend（Python）

#### Ruff（フォーマット + リント）

```bash
cd /workspace/backend

# フォーマット
uv run ruff format .

# リント
uv run ruff check .

# リント自動修正
uv run ruff check --fix .
```

#### pyright（型チェック）

```bash
cd /workspace/backend
uv run pyright
```

### Frontend（TypeScript）

#### Prettier（フォーマット）

```bash
cd /workspace/frontend
pnpm format
```

#### ESLint（リント）

```bash
cd /workspace/frontend
pnpm lint
```

---

## トラブルシューティング

### Q1. コンテナが起動しない

**原因**: Dockerリソース不足

**解決策**:
1. Docker Desktopの設定を開く
2. Resources → メモリを8GB以上に増やす
3. Docker Desktopを再起動

### Q2. `uv sync`が失敗する

**原因**: Python依存関係の競合

**解決策**:

```bash
cd /workspace/backend
rm -rf .venv
uv sync --all-extras
```

### Q3. `pnpm install`が失敗する

**原因**: Node.js依存関係の競合

**解決策**:

```bash
cd /workspace/frontend
rm -rf node_modules .pnpm-store
pnpm install
```

### Q4. PostgreSQLに接続できない

**原因**: dbコンテナが起動していない

**解決策**:

```bash
# コンテナ状態確認
docker ps

# dbコンテナが表示されない場合、再起動
docker compose -f .devcontainer/docker-compose.yml up -d db
```

### Q5. ポート8000/3000が使用中

**原因**: 別のプロセスがポートを使用中

**解決策**:

```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process
```

### Q6. VSCode拡張機能が動作しない

**原因**: DevContainer内に拡張機能がインストールされていない

**解決策**:
1. `Cmd+Shift+P` → 「Developer: Reload Window」
2. それでもダメなら: 「Dev Containers: Rebuild Container」

---

## VSCode設定

### 自動フォーマット（保存時）

`.vscode/settings.json`（既に設定済み）:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  }
}
```

### 推奨拡張機能（自動インストール済み）

- **Python**: `ms-python.python`
- **Pylance**: `ms-python.vscode-pylance`
- **Ruff**: `charliermarsh.ruff`
- **ESLint**: `dbaeumer.vscode-eslint`
- **Prettier**: `esbenp.prettier-vscode`
- **Tailwind CSS**: `bradlc.vscode-tailwindcss`
- **Docker**: `ms-azuretools.vscode-docker`
- **GitHub Copilot**: `github.copilot`

---

## データボリューム管理

### ボリューム一覧確認

```bash
docker volume ls | grep platinum-axe
```

### データベースデータ削除（全データ消去）

```bash
docker volume rm platinum-axe_postgres-data
```

**注意**: 開発中のデータが全て消えます。実行前にバックアップ推奨。

### Redisデータ削除

```bash
docker volume rm platinum-axe_redis-data
```

---

## パフォーマンスチューニング

### macOS Docker Desktop

**ファイル共有を高速化**:

`.devcontainer/docker-compose.yml`で`:cached`オプション使用（既に設定済み）:

```yaml
volumes:
  - ../:/workspace:cached
```

### Linux

**ネイティブパフォーマンス**: Linuxは追加設定不要で高速動作します。

### Windows

**WSL2使用推奨**:
1. WSL2を有効化
2. Docker Desktop for WindowsでWSL2バックエンドを有効化
3. プロジェクトをWSL2ファイルシステム内に配置

---

## 次のステップ

開発環境が起動したら、以下のタスクを進めてください:

1. **Alembicセットアップ**
   - `docs/backend/development-guide.md`を参照
   - 初回マイグレーションファイル作成
   - マイグレーション適用

2. **Backend API実装**
   - `docs/backend/structure.md`を参照
   - Health Check API実装
   - モックデータ返却API実装

3. **Frontend構築**
   - `docs/frontend/structure.md`を参照
   - Next.jsプロジェクト初期化
   - shadcn/ui導入

---

## 参考情報

- **VSCode Dev Containers公式ドキュメント**: https://code.visualstudio.com/docs/devcontainers/containers
- **Docker公式ドキュメント**: https://docs.docker.com/
- **uv公式ドキュメント**: https://github.com/astral-sh/uv
- **pnpm公式ドキュメント**: https://pnpm.io/

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
