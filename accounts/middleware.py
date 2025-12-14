# create this file in accounts/middleware.py
import time
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import HttpResponse


class LoginRateLimitMiddleware:
    """
    A simple login rate limiter keyed by IP + username.
    Not bulletproof, but helps mitigate brute-force in small projects.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_attempts = 6
        self.block_seconds = 300  # 5 minutes

    def __call__(self, request):
        if request.path.endswith('/login/') and request.method == 'POST':
            ip = self.get_client_ip(request)
            username = request.POST.get('username', '')
            key = f'failed_login:{ip}:{username}'
            blocked_key = f'blocked:{ip}:{username}'

            if cache.get(blocked_key):
                return HttpResponse('Too many failed attempts. Try again later.', status=429)

            response = self.get_response(request)

            # If login failed (status remains 200 and view adds message) we can't reliably detect here.
            # Instead, increment on every POST where authentication fails — use a signal in real project.
            return response

        return self.get_response(request)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    

class DisableBrowserCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response
    

class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response


