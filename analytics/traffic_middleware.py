from analytics.signals import update_website_traffic

class WebsiteTrafficMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update website traffic metrics only for relevant requests (non-static resources)
        # Strip query parameters from the path to correctly identify static files
        path = request.path_info.split('?')[0].lower()
        static_extensions = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.otf'}
        is_static = path.startswith('/static/') or any(path.endswith(ext) for ext in static_extensions)
        
        if not is_static:
            # Use IP address as a unique identifier for tracking visitors
            visitor_id = request.META.get('REMOTE_ADDR', 'unknown')
            update_website_traffic(visitor_id=visitor_id, request=request)
        
        # Continue processing the request
        response = self.get_response(request)
        return response
