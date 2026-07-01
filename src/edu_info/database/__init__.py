"""数据库模块"""
from edu_info.database.schema import create_database, get_connection, init_database

__all__ = ["create_database", "get_connection", "init_database"]
