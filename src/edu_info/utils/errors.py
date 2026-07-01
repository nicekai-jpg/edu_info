"""
错误处理模块

定义统一的错误处理机制，提供友好的错误信息
"""

from functools import wraps


class AppError(Exception):
    """应用错误基类"""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        user_message: str | None = None,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.user_message = user_message or message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "code": self.code,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
        }


# ========== 数据相关错误 ==========

class DataError(AppError):
    """数据错误基类"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="DATA_ERROR", **kwargs)


class DataImportError(DataError):
    """数据导入错误"""

    def __init__(
        self,
        message: str = "数据导入失败",
        field: str | None = None,
        **kwargs,
    ):
        user_msg = f"请检查{field or '数据文件'}格式是否正确" if field else message
        super().__init__(
            message=message,
            code="DATA_IMPORT_ERROR",
            user_message=user_msg,
            details={"field": field},
            **kwargs,
        )


class DataValidationError(DataError):
    """数据验证错误"""

    def __init__(
        self,
        message: str = "数据验证失败",
        field: str | None = None,
        value: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code="DATA_VALIDATION_ERROR",
            user_message=f"{field or '数据'}验证失败：{message}",
            details={"field": field, "value": value},
            **kwargs,
        )


class DataNotFoundError(DataError):
    """数据未找到错误"""

    def __init__(
        self,
        resource_type: str = "数据",
        resource_id: str | None = None,
        **kwargs,
    ):
        msg = f"{resource_type}未找到"
        if resource_id:
            msg += f" (ID: {resource_id})"

        super().__init__(
            message=msg,
            code="DATA_NOT_FOUND",
            user_message=f"找不到指定的{resource_type}",
            details={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs,
        )


class DatabaseError(DataError):
    """数据库操作错误"""

    def __init__(
        self,
        message: str = "数据库操作失败",
        operation: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            user_message="数据库操作失败，请稍后重试",
            details={"operation": operation},
            **kwargs,
        )


# ========== 规划引擎相关错误 ==========

class EngineError(AppError):
    """规划引擎错误基类"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="ENGINE_ERROR", **kwargs)


class InsufficientDataError(EngineError):
    """数据不足错误"""

    def __init__(
        self,
        message: str = "数据不足，无法进行规划分析",
        missing_data: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code="INSUFFICIENT_DATA",
            user_message="数据不足，请先导入必要的数据",
            details={"missing_data": missing_data or []},
            **kwargs,
        )


class PlanningError(EngineError):
    """规划分析错误"""

    def __init__(
        self,
        message: str = "规划分析失败",
        step: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code="PLANNING_ERROR",
            user_message="规划分析过程中出现错误",
            details={"step": step},
            **kwargs,
        )


# ========== 用户相关错误 ==========

class UserError(AppError):
    """用户操作错误基类"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="USER_ERROR", **kwargs)


class ProfileNotFoundError(UserError):
    """学生档案未找到"""

    def __init__(
        self,
        profile_id: str | None = None,
        **kwargs,
    ):
        msg = "学生档案不存在"
        if profile_id:
            msg += f" (ID: {profile_id})"

        super().__init__(
            message=msg,
            code="PROFILE_NOT_FOUND",
            user_message="找不到该学生档案，请检查是否已创建",
            details={"profile_id": profile_id},
            **kwargs,
        )


class ProfileValidationError(UserError):
    """学生档案验证错误"""

    def __init__(
        self,
        message: str = "学生档案信息不完整或有误",
        field: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code="PROFILE_VALIDATION_ERROR",
            user_message=f"{field or '档案信息'}填写有误，请检查后重试",
            details={"field": field},
            **kwargs,
        )


# ========== 配置相关错误 ==========

class ConfigError(AppError):
    """配置错误"""

    def __init__(
        self,
        message: str = "配置错误",
        config_key: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code="CONFIG_ERROR",
            user_message="系统配置有误，请联系管理员",
            details={"config_key": config_key},
            **kwargs,
        )


# ========== 错误处理装饰器 ==========


def handle_errors(default_error: type[AppError] | None = None):
    """
    错误处理装饰器

    Args:
        default_error: 默认错误类型

    Usage:
        @handle_errors(DataImportError)
        def import_data(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppError:
                # 已经是应用错误，直接抛出
                raise
            except Exception as e:
                # 其他异常转换为应用错误
                if default_error:
                    raise default_error(
                        message=str(e),
                        details={"exception_type": type(e).__name__},
                    ) from e
                else:
                    raise AppError(
                        message=str(e),
                        details={"exception_type": type(e).__name__},
                    ) from e

        return wrapper

    return decorator
