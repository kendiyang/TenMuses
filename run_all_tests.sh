#!/bin/bash

# TenMuses 综合测试执行脚本
# 自动启动后端和运行所有测试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 函数定义
print_header() {
    echo -e "\n${BLUE}${BOLD}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}$1${NC}"
    echo -e "${BLUE}${BOLD}════════════════════════════════════════════════════════${NC}\n"
}

print_section() {
    echo -e "\n${CYAN}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# 主程序开始
print_header "TenMuses 综合测试执行系统"

print_section "检查环境"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 未安装"
    exit 1
fi
print_success "Python 3 已安装"

# 检查 Redis
print_info "检查 Redis..."
if ! command -v redis-cli &> /dev/null && ! docker ps 2>/dev/null | grep -q redis; then
    print_warning "Redis 未运行"
    print_info "请启动 Redis: docker run -d -p 6379:6379 redis:7-alpine"
fi

# 进入工作目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
print_success "工作目录: $SCRIPT_DIR"

# 检查必要文件
print_section "检查测试文件"

if [ -f "integration_test_suite.py" ]; then
    print_success "集成测试脚本存在"
else
    print_error "集成测试脚本不存在"
    exit 1
fi

if [ -f "e2e_test_suite.py" ]; then
    print_success "E2E 测试脚本存在"
else
    print_error "E2E 测试脚本不存在"
    exit 1
fi

if [ -f "test_redis_cache.py" ]; then
    print_success "Redis 缓存测试脚本存在"
else
    print_error "Redis 缓存测试脚本不存在"
    exit 1
fi

# 启动后端服务
print_section "启动后端服务"

if [ -d "backend" ]; then
    cd backend
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        print_warning "虚拟环境不存在，请先运行："
        print_info "cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    
    # 激活虚拟环境
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    print_info "启动 FastAPI 服务..."
    python -m app.main > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    print_success "后端进程 PID: $BACKEND_PID"
    
    # 等待后端启动
    print_info "等待后端启动..."
    sleep 3
    
    # 检查后端是否成功启动
    if curl -s -m 2 http://localhost:8000/docs > /dev/null 2>&1; then
        print_success "后端服务已启动"
    else
        print_error "后端服务启动失败"
        print_error "日志: $(tail -20 /tmp/backend.log)"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    
    cd ..
else
    print_error "backend 目录不存在"
    exit 1
fi

# 运行测试
print_section "执行测试"

print_info "1. 运行 Redis 缓存测试..."
print_warning "（这个测试需要 Redis 运行）"
if python3 test_redis_cache.py; then
    print_success "Redis 缓存测试通过"
else
    print_warning "Redis 缓存测试失败（可能是 Redis 未运行）"
fi

print_info "\n2. 运行集成测试..."
if python3 integration_test_suite.py; then
    print_success "集成测试通过"
else
    print_error "集成测试失败"
fi

print_info "\n3. 运行端到端 (E2E) 测试..."
if python3 e2e_test_suite.py; then
    print_success "E2E 测试通过"
else
    print_error "E2E 测试失败"
fi

# 清理
print_section "清理"

if [ ! -z "$BACKEND_PID" ]; then
    print_info "关闭后端服务 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    sleep 1
    print_success "后端服务已关闭"
fi

# 总结
print_header "测试执行完成"
print_success "所有测试已运行"
print_info "详细日志请查看上述输出"

exit 0
