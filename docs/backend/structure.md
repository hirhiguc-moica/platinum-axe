# Backend構造 - DDD設計

## 概要

platinum-axeのBackendは、**DDD（Domain-Driven Design）** アーキテクチャを採用しています。

**参考**: jobsanプロジェクトの構成を踏襲

**技術スタック**:
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL 15
- Redis
- Python 3.12 + uv

---

## DDD 4層アーキテクチャ

```
┌─────────────────────────────────────────┐
│      Presentation Layer                 │  ← API・リクエスト/レスポンス
│      (app/presentation/)                │
└─────────────────┬───────────────────────┘
                  │ 依存
┌─────────────────▼───────────────────────┐
│      UseCase Layer                      │  ← アプリケーションロジック
│      (app/usecase/)                     │
└─────────────────┬───────────────────────┘
                  │ 依存
┌─────────────────▼───────────────────────┐
│      Domain Layer                       │  ← ビジネスロジック
│      (app/domain/)                      │
└─────────────────▲───────────────────────┘
                  │ 依存
┌─────────────────┴───────────────────────┐
│      Infrastructure Layer               │  ← DB・外部API・キャッシュ
│      (app/infrastructure/)              │
└─────────────────────────────────────────┘
```

**依存の方向**: `Presentation → UseCase → Domain ← Infrastructure`

**重要**: Domain層は他のどの層にも依存しない（Clean Architecture）

---

## 各層の責務

### 1. Domain Layer（ドメイン層）

**責務**: ビジネスロジックの中核

**含まれるもの**:
- ✅ ドメインモデル（エンティティ・値オブジェクト）
- ✅ リポジトリインターフェース（実装は持たない）
- ✅ ドメインサービス（ビジネスルール）

**依存**: なし（完全に独立）

#### ディレクトリ構造

```
app/domain/
├── __init__.py
├── models/                       # ドメインモデル
│   ├── __init__.py
│   ├── stock.py                  # 銘柄エンティティ
│   ├── round.py                  # ラウンドエンティティ
│   ├── recommendation.py         # 推奨銘柄エンティティ
│   ├── signal.py                 # デイリーシグナルエンティティ
│   └── technical_indicator.py    # テクニカル指標値オブジェクト
│
├── repositories/                 # リポジトリインターフェース（ABC）
│   ├── __init__.py
│   ├── stock_repository.py
│   ├── round_repository.py
│   ├── recommendation_repository.py
│   └── signal_repository.py
│
└── services/                     # ドメインサービス
    ├── __init__.py
    └── round_service.py          # ラウンド関連のビジネスルール
```

#### ドメインモデル例

```python
# app/domain/models/round.py
from dataclasses import dataclass
from datetime import date
from enum import Enum

class RoundType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class RoundStatus(Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

@dataclass
class Round:
    """ラウンドドメインモデル"""
    round_id: str
    round_type: RoundType
    start_date: date
    end_date: date
    status: RoundStatus
    model_version: str | None = None

    def is_active(self) -> bool:
        """ラウンドが現在アクティブか"""
        return self.status == RoundStatus.ACTIVE

    def close(self) -> None:
        """ラウンドをクローズ"""
        if self.status == RoundStatus.CLOSED:
            raise ValueError("Round is already closed")
        self.status = RoundStatus.CLOSED
```

#### リポジトリインターフェース例

```python
# app/domain/repositories/round_repository.py
from abc import ABC, abstractmethod
from app.domain.models.round import Round

class RoundRepository(ABC):
    """ラウンドリポジトリインターフェース"""

    @abstractmethod
    async def find_by_id(self, round_id: str) -> Round | None:
        """IDでラウンドを取得"""
        pass

    @abstractmethod
    async def find_active_rounds(self) -> list[Round]:
        """アクティブなラウンド一覧を取得"""
        pass

    @abstractmethod
    async def save(self, round: Round) -> Round:
        """ラウンドを保存"""
        pass
```

---

### 2. UseCase Layer（ユースケース層）

**責務**: アプリケーションロジック・ユースケースの実装

**含まれるもの**:
- ✅ ユースケース（1ユースケース = 1ファイル）
- ✅ ドメインモデルの組み立て・調整
- ✅ トランザクション管理

**依存**: Domain層のみ

#### ディレクトリ構造

```
app/usecase/
├── __init__.py
├── rounds/
│   ├── __init__.py
│   ├── get_rounds.py             # ラウンド一覧取得
│   ├── get_round_detail.py       # ラウンド詳細取得
│   └── get_round_results.py      # ラウンド結果取得
│
├── signals/
│   ├── __init__.py
│   └── get_daily_signals.py      # デイリーシグナル取得
│
└── stocks/
    ├── __init__.py
    ├── get_stock_list.py         # 銘柄一覧取得
    └── get_stock_detail.py       # 銘柄詳細取得
```

#### ユースケース例

```python
# app/usecase/rounds/get_rounds.py
from dataclasses import dataclass
from app.domain.repositories.round_repository import RoundRepository
from app.domain.models.round import Round, RoundType

@dataclass
class GetRoundsInput:
    """入力"""
    round_type: RoundType | None = None
    limit: int = 20

@dataclass
class GetRoundsOutput:
    """出力"""
    rounds: list[Round]
    total: int

class GetRoundsUseCase:
    """ラウンド一覧取得ユースケース"""

    def __init__(self, round_repository: RoundRepository):
        self.round_repository = round_repository

    async def execute(self, input: GetRoundsInput) -> GetRoundsOutput:
        """ユースケース実行"""
        if input.round_type:
            rounds = await self.round_repository.find_by_type(
                input.round_type,
                limit=input.limit
            )
        else:
            rounds = await self.round_repository.find_all(limit=input.limit)

        total = await self.round_repository.count()

        return GetRoundsOutput(rounds=rounds, total=total)
```

---

### 3. Infrastructure Layer（インフラ層）

**責務**: 外部システムとの連携実装

**含まれるもの**:
- ✅ リポジトリ実装（SQLAlchemy）
- ✅ DB接続・モデル定義
- ✅ Redis接続
- ✅ 外部API連携（J-Quants API等）

**依存**: Domain層（インターフェースを実装）

#### ディレクトリ構造

```
app/infrastructure/
├── __init__.py
├── database/
│   ├── __init__.py
│   ├── connection.py             # DB接続設定
│   ├── models.py                 # SQLAlchemyモデル（全テーブル）
│   └── repositories/             # リポジトリ実装
│       ├── __init__.py
│       ├── stock_repository_impl.py
│       ├── round_repository_impl.py
│       ├── recommendation_repository_impl.py
│       └── signal_repository_impl.py
│
├── cache/
│   ├── __init__.py
│   └── redis_client.py           # Redis接続
│
└── external/                     # 外部API（将来追加）
    ├── __init__.py
    └── jquants_client.py         # J-Quants APIクライアント
```

#### SQLAlchemyモデル例

```python
# app/infrastructure/database/models.py
from sqlalchemy import Column, String, Date, Enum, DateTime, DECIMAL, BigInteger
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class RoundModel(Base):
    """ラウンドテーブル"""
    __tablename__ = "rounds"

    round_id = Column(String(20), primary_key=True)
    round_type = Column(String(10), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    model_version = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class StockMasterModel(Base):
    """銘柄マスタテーブル"""
    __tablename__ = "stock_master"

    stock_code = Column(String(10), primary_key=True)
    company_name = Column(String(255), nullable=False)
    sector_code = Column(String(10))
    sector_name = Column(String(100))
    market_code = Column(String(10))
    market_name = Column(String(50))
    is_active = Column(Boolean, default=True)
    market_cap = Column(DECIMAL(15, 2))
    # ... その他のカラム
```

#### リポジトリ実装例

```python
# app/infrastructure/database/repositories/round_repository_impl.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.repositories.round_repository import RoundRepository
from app.domain.models.round import Round, RoundType, RoundStatus
from app.infrastructure.database.models import RoundModel

class RoundRepositoryImpl(RoundRepository):
    """ラウンドリポジトリ実装"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, round_id: str) -> Round | None:
        """IDでラウンドを取得"""
        stmt = select(RoundModel).where(RoundModel.round_id == round_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_domain(model)

    async def find_active_rounds(self) -> list[Round]:
        """アクティブなラウンド一覧を取得"""
        stmt = select(RoundModel).where(RoundModel.status == "ACTIVE")
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def save(self, round: Round) -> Round:
        """ラウンドを保存"""
        model = self._to_model(round)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: RoundModel) -> Round:
        """モデル → ドメインモデル変換"""
        return Round(
            round_id=model.round_id,
            round_type=RoundType(model.round_type),
            start_date=model.start_date,
            end_date=model.end_date,
            status=RoundStatus(model.status),
            model_version=model.model_version,
        )

    def _to_model(self, round: Round) -> RoundModel:
        """ドメインモデル → モデル変換"""
        return RoundModel(
            round_id=round.round_id,
            round_type=round.round_type.value,
            start_date=round.start_date,
            end_date=round.end_date,
            status=round.status.value,
            model_version=round.model_version,
        )
```

---

### 4. Presentation Layer（プレゼンテーション層）

**責務**: API・リクエスト/レスポンス処理

**含まれるもの**:
- ✅ FastAPI Router
- ✅ Pydanticスキーマ（バリデーション）
- ✅ 依存性注入（DI）
- ✅ OpenAPI自動生成

**依存**: UseCase層

#### ディレクトリ構造

```
app/presentation/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── dependencies.py           # FastAPI依存性注入
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py             # v1ルーター統合
│   │   ├── rounds.py             # ラウンドAPI
│   │   ├── signals.py            # シグナルAPI
│   │   └── stocks.py             # 銘柄API
│   └── health.py                 # ヘルスチェック
│
└── schemas/                      # Pydanticスキーマ
    ├── __init__.py
    ├── round.py
    ├── signal.py
    └── stock.py
```

#### Pydanticスキーマ例

```python
# app/presentation/schemas/round.py
from pydantic import BaseModel, Field
from datetime import date
from enum import Enum

class RoundTypeSchema(str, Enum):
    """ラウンドタイプ"""
    BUY = "BUY"
    SELL = "SELL"

class RoundStatusSchema(str, Enum):
    """ラウンドステータス"""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

class RoundResponse(BaseModel):
    """ラウンドレスポンス"""
    round_id: str = Field(..., description="ラウンドID", examples=["2025-W10-BUY"])
    round_type: RoundTypeSchema = Field(..., description="ラウンドタイプ")
    start_date: date = Field(..., description="開始日")
    end_date: date = Field(..., description="終了日")
    status: RoundStatusSchema = Field(..., description="ステータス")
    model_version: str | None = Field(None, description="モデルバージョン")

    class Config:
        json_schema_extra = {
            "example": {
                "round_id": "2025-W10-BUY",
                "round_type": "BUY",
                "start_date": "2025-03-03",
                "end_date": "2025-03-07",
                "status": "ACTIVE",
                "model_version": "v1.0"
            }
        }

class RoundsListResponse(BaseModel):
    """ラウンド一覧レスポンス"""
    rounds: list[RoundResponse]
    total: int
```

#### FastAPI Router例

```python
# app/presentation/api/v1/rounds.py
from fastapi import APIRouter, Depends, Query
from app.presentation.schemas.round import RoundsListResponse, RoundTypeSchema
from app.usecase.rounds.get_rounds import GetRoundsUseCase, GetRoundsInput
from app.presentation.api.dependencies import get_round_usecase

router = APIRouter(prefix="/rounds", tags=["rounds"])

@router.get(
    "",
    response_model=RoundsListResponse,
    summary="ラウンド一覧取得",
    description="ラウンドの一覧を取得します"
)
async def get_rounds(
    round_type: RoundTypeSchema | None = Query(None, description="ラウンドタイプ"),
    limit: int = Query(20, ge=1, le=100, description="取得件数"),
    usecase: GetRoundsUseCase = Depends(get_round_usecase)
) -> RoundsListResponse:
    """ラウンド一覧取得"""
    input = GetRoundsInput(
        round_type=round_type,
        limit=limit
    )
    output = await usecase.execute(input)

    return RoundsListResponse(
        rounds=[
            RoundResponse(
                round_id=r.round_id,
                round_type=r.round_type.value,
                start_date=r.start_date,
                end_date=r.end_date,
                status=r.status.value,
                model_version=r.model_version
            )
            for r in output.rounds
        ],
        total=output.total
    )
```

---

## 依存性注入（DI）

**使用ライブラリ**: `dependency-injector`（jobsanと同じ）

### DIコンテナ設定

```python
# app/container.py
from dependency_injector import containers, providers
from app.infrastructure.database.connection import get_async_session
from app.infrastructure.database.repositories.round_repository_impl import RoundRepositoryImpl
from app.usecase.rounds.get_rounds import GetRoundsUseCase

class Container(containers.DeclarativeContainer):
    """DIコンテナ"""

    wiring_config = containers.WiringConfiguration(
        modules=["app.presentation.api.dependencies"]
    )

    # Database
    db_session = providers.Resource(get_async_session)

    # Repositories
    round_repository = providers.Factory(
        RoundRepositoryImpl,
        session=db_session
    )

    # UseCases
    get_rounds_usecase = providers.Factory(
        GetRoundsUseCase,
        round_repository=round_repository
    )
```

### 依存性注入（FastAPI Depends）

```python
# app/presentation/api/dependencies.py
from fastapi import Depends
from app.container import Container
from app.usecase.rounds.get_rounds import GetRoundsUseCase

container = Container()

def get_round_usecase() -> GetRoundsUseCase:
    """ラウンドユースケース取得"""
    return container.get_rounds_usecase()
```

---

## データフロー

### リクエスト → レスポンスの流れ

```
1. Client
   ↓ HTTP Request
2. FastAPI Router (Presentation)
   ↓ Pydanticでバリデーション
3. UseCase (UseCase Layer)
   ↓ ビジネスロジック実行
4. Repository Interface (Domain Layer)
   ↓ 実装呼び出し
5. Repository Implementation (Infrastructure Layer)
   ↓ SQLAlchemy Query
6. PostgreSQL
   ↓ データ取得
7. Repository Implementation
   ↓ Domain Model変換
8. UseCase
   ↓ 結果返却
9. FastAPI Router
   ↓ Pydantic Response変換
10. Client
   ↓ HTTP Response
```

---

## OpenAPI自動生成

FastAPIは自動的にOpenAPI仕様を生成します。

### アクセス

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Frontend型生成

Frontendでは、このOpenAPI仕様から型を自動生成：

```bash
# frontendディレクトリで実行
pnpm generate
```

`@hey-api/openapi-ts`が`lib/api/generated/`に型定義を自動生成します。

---

## テスト戦略

### ユニットテスト

各層を独立してテスト：

```python
# tests/unit/usecase/test_get_rounds.py
import pytest
from app.usecase.rounds.get_rounds import GetRoundsUseCase, GetRoundsInput
from app.domain.models.round import Round, RoundType, RoundStatus
from datetime import date

@pytest.mark.asyncio
async def test_get_rounds(mocker):
    """ラウンド一覧取得テスト"""
    # モックリポジトリ
    mock_repo = mocker.Mock()
    mock_repo.find_all.return_value = [
        Round(
            round_id="2025-W10-BUY",
            round_type=RoundType.BUY,
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 7),
            status=RoundStatus.ACTIVE
        )
    ]
    mock_repo.count.return_value = 1

    # ユースケース実行
    usecase = GetRoundsUseCase(mock_repo)
    output = await usecase.execute(GetRoundsInput(limit=20))

    # アサーション
    assert len(output.rounds) == 1
    assert output.total == 1
```

### 統合テスト

APIエンドポイントをテスト：

```python
# tests/integration/api/test_rounds.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_rounds_api():
    """ラウンド一覧取得APIテスト"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/rounds")

    assert response.status_code == 200
    data = response.json()
    assert "rounds" in data
    assert "total" in data
```

---

## ベストプラクティス

### 1. 各層の責務を守る

❌ **NG**: UseCaseでSQLAlchemyを直接使う

```python
# NG例
class GetRoundsUseCase:
    async def execute(self):
        result = await session.execute(select(RoundModel))  # NG!
```

✅ **OK**: Repositoryインターフェース経由

```python
# OK例
class GetRoundsUseCase:
    def __init__(self, round_repository: RoundRepository):
        self.round_repository = round_repository

    async def execute(self):
        rounds = await self.round_repository.find_all()  # OK!
```

### 2. ドメインモデルとDBモデルを分離

- ドメインモデル: ビジネスロジックを持つ
- DBモデル: データ永続化のみ
- 変換はRepositoryで実施

### 3. トランザクション管理

UseCaseでトランザクション境界を定義：

```python
async def execute(self):
    async with self.session.begin():  # トランザクション開始
        # 複数のRepository操作
        await self.round_repository.save(round)
        await self.recommendation_repository.save_all(recommendations)
    # commit
```

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
