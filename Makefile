.PHONY: install run test lint format clean help

# 安装依赖
install:
	uv sync

# 本地执行批量规划报告生成
run:
	uv run python scripts/generate_reports.py

# 运行单元测试
test:
	uv run pytest tests/ -v

# 静态代码检查
lint:
	uv run ruff check src/edu_info tests

# 代码格式化
format:
	uv run ruff format src/edu_info tests

# 清理缓存与临时文件
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} \;
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} \;
	find . -type d -name "*.egg-info" -delete
	rm -rf htmlcov/
	rm -rf .coverage

# 帮助菜单
help:
	@echo "可用命令:"
	@echo "  make install   - 安装依赖包"
	@echo "  make run       - 本地执行批量规划计算并生成报告"
	@echo "  make test      - 运行测试用例"
	@echo "  make lint      - 代码格式与类型检查"
	@echo "  make format    - 自动格式化代码"
	@echo "  make clean     - 清理本地缓存"
