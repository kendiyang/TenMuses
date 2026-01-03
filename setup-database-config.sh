#!/bin/bash
# TenMuses 数据库配置设置向导

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    TenMuses 数据库配置设置向导                              ║${NC}"
echo -e "${BLUE}║    OPENAI_API_KEY & OPENAI_BASE_URL 数据库读取              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. 检查环境
echo -e "${YELLOW}[Step 1/5] 检查环境...${NC}"
echo ""

if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}✗ Python 虚拟环境不存在${NC}"
    echo "  请运行以下命令："
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r backend/requirements.txt"
    exit 1
fi
echo -e "${GREEN}✓ Python 虚拟环境已安装${NC}"

# 检查数据库
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}⚠ .env 文件不存在，使用默认值${NC}"
    echo "  建议创建 $BACKEND_DIR/.env 文件"
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

echo ""

# 2. 检查配置文件
echo -e "${YELLOW}[Step 2/5] 检查配置文件...${NC}"
echo ""

CONFIG_FILES=(
    "backend/app/services/config_service.py"
    "backend/app/api/v1/config.py"
    "init-llm-config.py"
    "test-db-config.py"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (缺失)"
        exit 1
    fi
done

echo ""

# 3. 启动数据库和后端
echo -e "${YELLOW}[Step 3/5] 启动后端服务...${NC}"
echo ""

# 检查后端是否已运行
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端已运行${NC}"
else
    echo "  启动后端服务中..."
    cd "$BACKEND_DIR"
    $VENV_PYTHON -m uvicorn app.main:app --reload --port 8000 > /tmp/tenmuses-backend.log 2>&1 &
    BACKEND_PID=$!
    echo "  等待后端启动..."
    sleep 5
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端启动成功 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}✗ 后端启动失败${NC}"
        echo "  查看日志: tail -f /tmp/tenmuses-backend.log"
        exit 1
    fi
fi

echo ""

# 4. 运行测试
echo -e "${YELLOW}[Step 4/5] 测试配置功能...${NC}"
echo ""

cd "$SCRIPT_DIR"
if $VENV_PYTHON test-db-config.py; then
    echo ""
    echo -e "${GREEN}✓ 所有测试通过${NC}"
else
    echo ""
    echo -e "${RED}✗ 测试失败${NC}"
    echo "  请查看上方错误信息"
    exit 1
fi

echo ""

# 5. 设置配置
echo -e "${YELLOW}[Step 5/5] 配置 LLM API Key...${NC}"
echo ""

read -p "是否要设置 OpenAI API Key? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash "$SCRIPT_DIR/setup-llm-config.sh"
else
    echo "  跳过 OpenAI 配置"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ 设置完成！${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "接下来的步骤："
echo ""
echo "1. 启动后端服务："
echo "   cd backend && uvicorn app.main:app --reload"
echo ""
echo "2. 启动前端："
echo "   cd frontend && npm run dev"
echo ""
echo "3. 验证配置已保存："
echo "   curl -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "        http://localhost:8000/api/v1/config/llm/providers"
echo ""
echo "4. 现在可以使用 Copilot 功能了！"
echo ""

echo "文档："
echo "  - 快速参考: QUICK_DB_CONFIG_GUIDE.md"
echo "  - 完整文档: DATABASE_CONFIG_GUIDE.md"
echo "  - 实现细节: DATABASE_CONFIG_IMPLEMENTATION.md"
echo ""
