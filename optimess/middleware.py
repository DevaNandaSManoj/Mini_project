from django.shortcuts import redirect
from django.urls import reverse


# Role → named URL mapping
ROLE_DASHBOARD = {
    'student': 'student_dashboard',
    'warden':  'warden_dashboard',
    'mess':    'mess_dashboard',
    'admin':   'admin_dashboard',
}


class NoCacheMiddleware:
    """
    1. Adds Cache-Control: no-store to every response so the browser
       never caches any page (authenticated or not).  This means pressing
       the Back button always re-requests the URL from the server instead
       of showing a stale cached page.

    2. If an authenticated user hits the login URL, redirect them straight
       to their role-specific dashboard so the Back button never drops them
       back on the login screen.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ── Guard: bounce authenticated users away from login ──────────
        login_url = reverse('login')
        if request.path == login_url and request.user.is_authenticated:
            dashboard = ROLE_DASHBOARD.get(getattr(request.user, 'role', ''))
            if dashboard:
                return redirect(dashboard)

        response = self.get_response(request)

        # ── No-cache headers on every response ─────────────────────────
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response
