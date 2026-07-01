"""
配置管理模块

使用 pydantic-settings 管理应用配置
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ========== 应用配置 ==========

    app_name: str = Field(default="智能升学规划系统", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")

    # ========== 数据库配置 ==========

    db_path: str = Field(
        default="data/processed/edu_planning.duckdb",
        description="数据库文件路径"
    )

    # ========== 数据目录配置 ==========

    data_dir: str = Field(default="data", description="数据根目录")
    raw_data_dir: str = Field(default="data/raw", description="原始数据目录")
    processed_data_dir: str = Field(default="data/processed", description="处理后数据目录")
    routes_dir: str = Field(default="data/routes", description="路线数据目录")

    # ========== 日志配置 ==========

    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str | None = Field(default=None, description="日志文件路径")

    # ========== Streamlit 配置 ==========

    server_port: int = Field(default=8501, description="Streamlit 服务器端口")
    server_headless: bool = Field(default=True, description="无头模式")

    # ========== 规划引擎配置 ==========

    # 匹配权重
    weight_interest: float = Field(default=0.40, description="兴趣匹配权重")
    weight_ability: float = Field(default=0.25, description="能力匹配权重")
    weight_economic: float = Field(default=0.20, description="经济匹配权重")
    weight_time: float = Field(default=0.10, description="时间匹配权重")
    weight_region: float = Field(default=0.05, description="地域匹配权重")

    # 目标数量
    top_routes_count: int = Field(default=10, description="推荐路线数量")
    targets_per_route: int = Field(default=3, description="每条路线的目标数量（高/中/低）")

    @property
    def project_root(self) -> Path:
        """获取项目根目录"""
        return Path(__file__).parent.parent.parent.parent

    @property
    def full_db_path(self) -> Path:
        """获取完整数据库路径"""
        if Path(self.db_path).is_absolute():
            return Path(self.db_path)
        return self.project_root / self.db_path

    @property
    def full_data_dir(self) -> Path:
        """获取完整数据目录路径"""
        return self.project_root / self.data_dir

    def get_match_weights(self) -> dict[str, float]:
        """获取匹配权重配置"""
        return {
            "interest": self.weight_interest,
            "ability": self.weight_ability,
            "economic": self.weight_economic,
            "time": self.weight_time,
            "region": self.weight_region,
        }

    def validate_weights(self) -> bool:
        """验证权重和是否为 1.0"""
        total = (
            self.weight_interest +
            self.weight_ability +
            self.weight_economic +
            self.weight_time +
            self.weight_region
        )
        return abs(total - 1.0) < 0.001


# 全局配置实例
_config: Config | None = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """重新加载配置"""
    global _config
    _config = Config()
    return _config
