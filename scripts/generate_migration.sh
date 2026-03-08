#!/usr/bin/env bash
# 自动生成数据库迁移脚本
# 用法: ./scripts/generate_migration.sh "描述信息"
# 示例: ./scripts/generate_migration.sh "add user table"
#
# 前提: PostgreSQL 已运行，且 .env 中 DATABASE_URL 配置正确
# 该脚本会对比 SQLAlchemy 模型与数据库当前状态，自动生成差异迁移

set -e

if [ -z "$1" ]; then
    echo "用法: $0 <迁移描述>"
    echo "示例: $0 \"initial_tables\""
    exit 1
fi

cd "$(dirname "$0")/.."

echo "检查数据库是否存在..."
uv run python scripts/ensure_database.py

echo "正在生成迁移脚本: $1"
uv run alembic revision --autogenerate -m "$1"
echo "迁移脚本已生成，请检查 alembic/versions/ 目录"
echo ""
echo "应用迁移请运行: uv run alembic upgrade head"
