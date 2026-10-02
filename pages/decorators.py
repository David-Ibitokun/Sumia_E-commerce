"""Access control decorators shared by the apps.

`login_required` only proves *who* the visitor is; these decorators also check
*what* they are allowed to be. The user model carries an `account_type`, so a
vendor-only page must reject a signed in customer as firmly as it rejects an
anonymous visitor.

Lives in the `pages` app because both `shop` and `authentications` already
depend on it for `pages.models`.
"""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

#: Values of `UsersRegistration.account_type`.
VENDOR = 'vendor'
CUSTOMER = 'user'


def account_required(account_type, login_url='login'):
    """Build a decorator restricting a view to a single account type.

    Anonymous visitors are sent to the login page (with ``next`` preserved) so
    they can come back after authenticating. A signed in account of the wrong
    type is denied with 403: they are known, so bouncing them to login would
    loop.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url)

            if getattr(user, 'account_type', None) != account_type:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def vendor_required(view_func):
    """Allow the view only to a signed in vendor account."""
    return account_required(VENDOR)(view_func)


def customer_required(view_func):
    """Allow the view only to a signed in shopper account."""
    return account_required(CUSTOMER)(view_func)
