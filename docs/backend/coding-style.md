# Backend コーディング規約

**最終更新**: 2026-07-21

---

## 概要

Python 3.12 + FastAPI + SQLAlchemy 2.0を使用したBackend開発のコーディング規約です。

---

## ツール構成

### フォーマッター: Ruff

```bash
# フォーマット実行
uv run ruff format .

# チェックのみ
uv run ruff format --check .
```

### リンター: Ruff

```bash
# リント実行
uv run ruff check .

# 自動修正
uv run ruff check --fix .
```

### 型チェッカー: pyright

```bash
# 型チェック実行
uv run pyright
```

---

## 基本スタイル

### インデント・改行

- **インデント**: スペース4つ
- **行長**: 100文字以内（`pyproject.toml`で設定済み）
- **改行**: Unix形式（LF）

### インポート

**順序**（Ruffが自動整理）:

1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール

```python
# 標準ライブラリ
from datetime import date, datetime
from typing import Optional

# サードパーティライブラリ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# ローカルモジュール
from app.domain.round.entity import Round
from app.usecase.round.get_rounds import GetRoundsUseCase
```

### 文字列

- **シングルクォート**: 基本的に`'`を使用
- **ダブルクォート**: docstring, SQL文等で使用
- **f-string**: 文字列補間は f-string を推奨

```python
# Good
name = 'トヨタ自動車'
message = f'{name}の株価は{price}円です'

# Bad
name = "トヨタ自動車"
message = name + "の株価は" + str(price) + "円です"
```

---

## 型ヒント

### 基本方針

**全ての関数に型ヒントを記載する**

```python
# Good
def get_stock_price(stock_code: str, date: date) -> Decimal:
    ...

# Bad
def get_stock_price(stock_code, date):
    ...
```

### Python 3.12の型ヒント機能を活用

```python
from typing import Optional, Union

# Python 3.10+: Union型をパイプで表現
def get_stock(stock_code: str) -> Stock | None:
    ...

# Optional型
def get_stock_name(stock_code: str, default: str | None = None) -> str:
    ...
```

### generics

```python
from typing import Generic, TypeVar

T = TypeVar('T')

class Repository(Generic[T]):
    async def find_by_id(self, id: int) -> T | None:
        ...
```

---

## 命名規則

### 変数・関数名

- **スネークケース**: `stock_code`, `get_rounds`
- **説明的な名前**: 略語は避ける

```python
# Good
stock_code = '7203'
predicted_return = 5.5

# Bad
sc = '7203'
pred_ret = 5.5
```

### クラス名

- **パスカルケース**: `Round`, `StockPrice`

```python
class RoundRecommendation:
    ...
```

### 定数

- **大文字スネークケース**: `MAX_RECOMMENDATIONS = 10`

```python
MAX_BUY_RECOMMENDATIONS = 10
MAX_SELL_RECOMMENDATIONS = 10
DEFAULT_CONFIDENCE_THRESHOLD = 80.0
```

### プライベート変数

- **アンダースコアプレフィックス**: `_internal_cache`

```python
class StockService:
    def __init__(self):
        self._cache: dict[str, Stock] = {}
```

---

## DDD構造に従った実装

### ドメインエンティティ（domain/）

**原則**: ビジネスロジックをカプセル化

```python
from dataclasses import dataclass
from datetime import date
from enum import Enum

class RoundType(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'

class RoundStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'

@dataclass
class Round:
    """ラウンドエンティティ"""
    round_id: str
    round_type: RoundType
    start_date: date
    end_date: date
    status: RoundStatus

    def is_active(self) -> bool:
        """アクティブなラウンドかどうか"""
        return self.status == RoundStatus.ACTIVE

    def complete(self) -> None:
        """ラウンドを完了する"""
        if not self.is_active():
            raise ValueError('Already completed round cannot be completed again')
        self.status = RoundStatus.COMPLETED
```

### リポジトリインターフェース（domain/）

**原則**: 抽象化されたデータアクセス層

```python
from abc import ABC, abstractmethod

class RoundRepository(ABC):
    """ラウンドリポジトリインターフェース"""

    @abstractmethod
    async def find_by_id(self, round_id: str) -> Round | None:
        """IDでラウンドを検索"""
        ...

    @abstractmethod
    async def find_active_rounds(self) -> list[Round]:
        """アクティブなラウンドを全て取得"""
        ...

    @abstractmethod
    async def save(self, round: Round) -> None:
        """ラウンドを保存"""
        ...
```

### リポジトリ実装（infrastructure/）

**原則**: SQLAlchemy 2.0の非同期APIを使用

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.round.entity import Round
from app.domain.round.repository import RoundRepository
from app.infrastructure.database.models import RoundModel

class RoundRepositoryImpl(RoundRepository):
    """ラウンドリポジトリ実装"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, round_id: str) -> Round | None:
        stmt = select(RoundModel).where(RoundModel.round_id == round_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def find_active_rounds(self) -> list[Round]:
        stmt = select(RoundModel).where(RoundModel.status == 'ACTIVE')
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def save(self, round: Round) -> None:
        model = self._to_model(round)
        self._session.add(model)
        await self._session.commit()

    def _to_entity(self, model: RoundModel) -> Round:
        """モデルをエンティティに変換"""
        return Round(
            round_id=model.round_id,
            round_type=RoundType(model.round_type),
            start_date=model.start_date,
            end_date=model.end_date,
            status=RoundStatus(model.status),
        )

    def _to_model(self, entity: Round) -> RoundModel:
        """エンティティをモデルに変換"""
        return RoundModel(
            round_id=entity.round_id,
            round_type=entity.round_type.value,
            start_date=entity.start_date,
            end_date=entity.end_date,
            status=entity.status.value,
        )
```

### ユースケース（usecase/）

**原則**: ビジネスロジックの組み合わせ

```python
from app.domain.round.entity import Round, RoundType
from app.domain.round.repository import RoundRepository

class GetRoundsUseCase:
    """ラウンド一覧取得ユースケース"""

    def __init__(self, round_repository: RoundRepository):
        self._round_repository = round_repository

    async def execute(self, round_type: RoundType | None = None) -> list[Round]:
        """ラウンド一覧を取得"""
        # アクティブなラウンドを取得
        rounds = await self._round_repository.find_active_rounds()

        # タイプでフィルタリング
        if round_type is not None:
            rounds = [r for r in rounds if r.round_type == round_type]

        return rounds
```

### API（presentation/api/v1/）

**原則**: FastAPIのルーターを使用

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.round.entity import RoundType
from app.infrastructure.database.session import get_db_session
from app.infrastructure.database.repositories import RoundRepositoryImpl
from app.usecase.round.get_rounds import GetRoundsUseCase

router = APIRouter(prefix='/rounds', tags=['rounds'])

@router.get('/')
async def get_rounds(
    round_type: RoundType | None = Query(None, description='ラウンドタイプ'),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """ラウンド一覧を取得"""
    # リポジトリ・ユースケース初期化
    round_repository = RoundRepositoryImpl(session)
    use_case = GetRoundsUseCase(round_repository)

    # ユースケース実行
    rounds = await use_case.execute(round_type)

    # レスポンス変換
    return [
        {
            'round_id': r.round_id,
            'round_type': r.round_type.value,
            'start_date': r.start_date.isoformat(),
            'end_date': r.end_date.isoformat(),
            'status': r.status.value,
        }
        for r in rounds
    ]
```

---

## SQLAlchemy 2.0ベストプラクティス

### 非同期セッション使用

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine('postgresql+asyncpg://...')
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

### SELECT文

```python
from sqlalchemy import select

# 基本的なSELECT
stmt = select(StockPriceModel).where(StockPriceModel.stock_code == '7203')
result = await session.execute(stmt)
models = result.scalars().all()

# JOINを使用
stmt = (
    select(RoundModel, RoundRecommendationModel)
    .join(RoundRecommendationModel, RoundModel.id == RoundRecommendationModel.round_id)
    .where(RoundModel.status == 'ACTIVE')
)
result = await session.execute(stmt)
rows = result.all()
```

### INSERT/UPDATE

```python
# INSERT
model = StockPriceModel(stock_code='7203', date=date.today(), close=2500)
session.add(model)
await session.commit()

# UPDATE
stmt = select(StockPriceModel).where(StockPriceModel.id == 1)
result = await session.execute(stmt)
model = result.scalar_one()
model.close = 2550
await session.commit()
```

---

## エラーハンドリング

### 例外クラスの定義

```python
class PlatinumAxeException(Exception):
    """基底例外クラス"""
    pass

class RoundNotFoundException(PlatinumAxeException):
    """ラウンドが見つからない"""
    pass

class InvalidRoundStatusException(PlatinumAxeException):
    """無効なラウンドステータス"""
    pass
```

### FastAPIでのエラーハンドリング

```python
from fastapi import HTTPException, status

@router.get('/{round_id}')
async def get_round(round_id: str, session: AsyncSession = Depends(get_db_session)):
    round_repository = RoundRepositoryImpl(session)
    round = await round_repository.find_by_id(round_id)

    if round is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Round {round_id} not found'
        )

    return {'round_id': round.round_id, ...}
```

---

## ロギング

### 基本方針

```python
import logging

logger = logging.getLogger(__name__)

async def get_rounds(round_type: RoundType | None = None):
    logger.info(f'Getting rounds: round_type={round_type}')

    try:
        rounds = await round_repository.find_active_rounds()
        logger.info(f'Found {len(rounds)} rounds')
        return rounds
    except Exception as e:
        logger.error(f'Failed to get rounds: {e}', exc_info=True)
        raise
```

---

## テスト

### pytest + pytest-asyncio

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.round.entity import Round, RoundType, RoundStatus
from app.infrastructure.database.repositories import RoundRepositoryImpl

@pytest.mark.asyncio
async def test_find_active_rounds(db_session: AsyncSession):
    """アクティブなラウンドを取得できる"""
    # Arrange
    repository = RoundRepositoryImpl(db_session)

    # Act
    rounds = await repository.find_active_rounds()

    # Assert
    assert len(rounds) > 0
    assert all(r.is_active() for r in rounds)
```

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
