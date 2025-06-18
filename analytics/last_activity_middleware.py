from django.utils import timezone

class LastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.session_key:
            request.session['last_activity'] = timezone.now().isoformat()
            request.session.modified = True
        response = self.get_response(request)
        return response
