#!/usr/bin/env bash
# 应用所有待执行的数据库迁移
# 用法: ./scripts/migrate.sh
#
# 前提: PostgreSQL 已运行，且 .env 中 DATABASE_URL 配置正确

set -e

cd "$(dirname "$0")/.."

echo "检查数据库是否存在..."
uv run python scripts/ensure_database.py

echo "正在应用数据库迁移..."
uv run alembic upgrade head
echo "迁移完成"
