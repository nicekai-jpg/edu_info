#!/bin/bash
# 升学规划系统 - 快速启动脚本
# 使用方法：./scripts/start.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}   升学规划咨询系统 - 启动脚本${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 1. 检查数据库
echo -e "${YELLOW}[1/4] 检查数据库状态...${NC}"
if [ ! -f "data/duckdb/edu_planning.db" ]; then
    echo -e "${RED}❌ 数据库不存在，正在初始化...${NC}"
    uv run python scripts/init_database.py
else
    echo -e "${GREEN}✅ 数据库已存在${NC}"
fi

# 2. 检查依赖
echo -e "${YELLOW}[2/4] 检查依赖...${NC}"
if ! uv run python -c "import streamlit; import duckdb; import pandas" 2>/dev/null; then
    echo -e "${RED}❌ 依赖未安装，正在安装...${NC}"
    uv sync
else
    echo -e "${GREEN}✅ 依赖已安装${NC}"
fi

# 3. 显示数据库统计
echo -e "${YELLOW}[3/4] 数据库统计:${NC}"
uv run python -c "
import duckdb
conn = duckdb.connect('data/duckdb/edu_planning.db')
print(f'  高校：{conn.execute(\"SELECT COUNT(*) FROM universities\").fetchone()[0]}')
print(f'  专业：{conn.execute(\"SELECT COUNT(*) FROM majors\").fetchone()[0]}')
print(f'  学生：{conn.execute(\"SELECT COUNT(*) FROM students\").fetchone()[0]}')
print(f'  2025 分数：{conn.execute(\"SELECT COUNT(*) FROM admission_scores WHERE year=2025\").fetchone()[0]}')
print(f'  规划路线：{conn.execute(\"SELECT COUNT(*) FROM planning_routes\").fetchone()[0]}')
conn.close()
"

# 4. 启动应用
echo -e "${YELLOW}[4/4] 启动 Streamlit 应用...${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  应用即将启动...${NC}"
echo -e "${GREEN}  访问地址：http://localhost:8501${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 启动 Streamlit
uv run streamlit run src/edu_info/main.py --server.port=8501
