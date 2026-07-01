.PHONY: install dev run test lint format clean help init-db

# 安装依赖
install:
	uv sync

# 开发模式
dev:
	uv sync --dev

# 启动 Streamlit
run:
	uv run streamlit run src/edu_info/main.py --server.port=8501

# 初始化数据库
init-db:
	uv run python scripts/init_database.py

# 运行测试
test:
	uv run pytest tests/ -v

# 代码检查
lint:
	uv run ruff check src/edu_info tests

# 格式化代码
format:
	uv run ruff format src/edu_info tests

# 清理
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} \;
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} \;
	find . -type d -name "*.egg-info" -delete
	rm -rf htmlcov/
	rm -rf .coverage

# 帮助
help:
	@echo "可用命令:"
	@echo "  make install   - 安装依赖"
	@echo "  make dev       - 开发模式安装"
	@echo "  make run       - 启动 Streamlit"
	@echo "  make init-db   - 初始化数据库"
	@echo "  make test      - 运行测试"
	@echo "  make lint      - 代码检查"
	@echo "  make format    - 格式化代码"
	@echo "  make clean     - 清理缓存"
