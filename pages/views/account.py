"""Account related pages.

Login, logout, registration and profile editing are handled by the
`authentications` app; this module only covers the remaining account screens.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url='login')
def my_account(request):
    """Overview of the signed in user's account."""
    return render(request, 'accounts/my_account.html')
