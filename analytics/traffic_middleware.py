from analytics.signals import update_website_traffic

class WebsiteTrafficMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update website traffic metrics for each request
        update_website_traffic()
        
        # Continue processing the request
        response = self.get_response(request)
        return response
