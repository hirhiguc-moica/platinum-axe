FROM python:3.12-bookworm

# Node.js 22のインストール
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs

# 基本ツールのインストール
RUN apt-get update && apt-get install -y \
    git \
    vim \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# uvのインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# pnpmのインストール
RUN npm install -g pnpm

# 作業ディレクトリ
WORKDIR /workspace

# non-rootユーザー作成（セキュリティ向上のため）
RUN useradd -m -s /bin/bash vscode && \
    chown -R vscode:vscode /workspace

USER vscode

# uvをインストール（vscodeユーザー用）
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# PATHを設定（uvは~/.local/binにインストールされる）
ENV PATH="/home/vscode/.local/bin:$PATH"
