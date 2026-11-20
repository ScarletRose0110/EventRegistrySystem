from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def roles_required(*roles):
    """US-06-AC5 / BR06: kiểm tra role ở máy chủ, kể cả truy cập thẳng URL."""
    def wrapper(fn):
        @wraps(fn)
        @login_required
        def decorated(*args, **kwargs):
            if not any(current_user.has_role(role) for role in roles):
                abort(403)  # "Bạn không có quyền truy cập chức năng này"
            return fn(*args, **kwargs)
        return decorated
    return wrapper
