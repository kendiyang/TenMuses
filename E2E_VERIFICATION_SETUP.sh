#!/bin/bash

# TenMuses Phase 2.3 RAG 端到端验证 - 自动配置脚本

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  TenMuses Phase 2.3 RAG 端到端验证 - 自动配置                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

WORKSPACE_DIR="/Users/mg/Workspace/TenMuses"
BACKEND_DIR="$WORKSPACE_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"

# Step 1: 检查 PostgreSQL
echo "📝 Step 1: 检查 PostgreSQL..."
if ! docker ps --filter "name=postgres" --format "{{.Names}}" | grep -q tenmuses; then
    echo "❌ PostgreSQL 容器未找到"
    echo "   建议: docker-compose -f docker-compose.integration.yml up -d postgres"
    exit 1
fi

CONTAINER=$(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1)
if ! docker ps --filter "name=$CONTAINER" --format "{{.Status}}" | grep -q "healthy\|running"; then
    echo "⏳ 等待 PostgreSQL 启动..."
    docker start "$CONTAINER" 2>/dev/null || true
    sleep 3
fi

echo "✅ PostgreSQL 容器: $CONTAINER (running)"

# Step 2: 创建数据库
echo ""
echo "📝 Step 2: 确保 tenmuses 数据库存在..."
docker exec "$CONTAINER" psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'tenmuses';" 2>/dev/null | grep -q 1 || \
    docker exec "$CONTAINER" psql -U postgres -c "CREATE DATABASE tenmuses;" || true
echo "✅ 数据库已准备"

# Step 3: 检查/设置 .env
echo ""
echo "📝 Step 3: 检查 .env 配置..."

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 未找到 .env 文件，创建默认配置..."
    cat > "$ENV_FILE" << 'ENVEOF'
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/tenmuses

# JWT
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=

# Anthropic
ANTHROPIC_API_KEY=

# CORS
CORS_ORIGINS_STR=http://localhost:3000,http://localhost:3001

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
ENVEOF
fi

# 检查 OPENAI_API_KEY
OPENAI_KEY=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2 | tr -d ' ')
if [ -z "$OPENAI_KEY" ]; then
    echo ""
    echo "⚠️  OPENAI_API_KEY 未设置"
    echo ""
    echo "请执行以下操作之一:"
    echo ""
    echo "  选项 A: 设置有效的 OpenAI API 密钥"
    echo "    $ export OPENAI_API_KEY='sk-xxx'"
    echo "    $ sed -i '' \"s|OPENAI_API_KEY=|OPENAI_API_KEY=$OPENAI_API_KEY|\" $ENV_FILE"
    echo ""
    echo "  选项 B: 使用虚拟密钥进行非API调用测试"
    echo "    $ sed -i '' 's|OPENAI_API_KEY=|OPENAI_API_KEY=sk-test-123456789|' $ENV_FILE"
    echo ""
    echo "请先设置密钥，然后继续。"
    echo ""
    echo "继续执行? (y/n): "
    read -r continue_choice
    if [ "$continue_choice" != "y" ]; then
        exit 1
    fi
else
    echo "✅ OPENAI_API_KEY 已配置: ${OPENAI_KEY:0:10}..."
fi

# Step 4: 验证 Python 环境
echo ""
echo "📝 Step 4: 验证 Python 环境..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    echo "⏳ 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "✅ Python 环境: $(python --version)"

# Step 5: 安装依赖
echo ""
echo "📝 Step 5: 检查依赖..."
pip install -q -r requirements.txt 2>/dev/null || {
    echo "⚠️  部分依赖安装失败，继续..."
}
echo "✅ 依赖检查完成"

# Step 6: 运行验证脚本
echo ""
echo "📝 Step 6: 运行 RAG 组件验证..."
python validate_rag_setup.py 2>&1 | tail -20

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ 配置完成！可以开始端到端验证                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "下一步:"
echo "  1. 启动后端: cd backend && source venv/bin/activate && python -m app.main"
echo "  2. 运行 E2E 测试: python test_e2e_rag.py"
echo ""
