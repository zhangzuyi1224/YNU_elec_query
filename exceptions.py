"""自定义异常。"""


class CredentialFormatError(ValueError):
    """password.txt 格式错误。"""


class LoginError(RuntimeError):
    """登录失败。"""


class CaptchaError(LoginError):
    """验证码识别或校验失败。"""


class AccountAuthError(LoginError):
    """账号密码错误。"""


class ParseError(RuntimeError):
    """页面或接口解析失败。"""


class QueryError(RuntimeError):
    """电费查询失败。"""
