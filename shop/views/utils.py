"""Helpers shared by the shop views."""
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def redirect_back(request, fallback):
    """Redirect to the referring page, falling back when it is not usable.

    Guards against open redirects: only same-host referrers are followed.
    """
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    return redirect(fallback)


def json_error(message, status=400):
    """Uniform error payload for the AJAX endpoints.

    The client reads ``status`` and ``message`` for the toast.
    """
    return JsonResponse({'status': 'error', 'message': message}, status=status)
