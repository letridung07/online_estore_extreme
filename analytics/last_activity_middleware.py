from django.utils import timezone
from django.conf import settings

class LastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip session creation and updates for static asset requests
        if not request.path_info.startswith(settings.STATIC_URL):
            if not request.session.session_key:
                request.session.create()
            request.session['last_activity'] = timezone.now().isoformat()
            request.session.modified = True
        response = self.get_response(request)
        return response
