from analytics.signals import update_website_traffic
import logging

# Configure logger for traffic middleware
logger = logging.getLogger(__name__)

class WebsiteTrafficMiddleware:
    STATIC_EXTENSIONS = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.otf'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update website traffic metrics only for relevant requests (non-static resources)
        # Strip query parameters from the path to correctly identify static files
        path = request.path_info.split('?')[0].lower()
        is_static = path.startswith('/static/') or any(path.endswith(ext) for ext in self.STATIC_EXTENSIONS)
        
        if not is_static:
            # Use session key as a unique identifier for tracking visitors (more accurate than IP)
            # Access session to ensure it exists; this will create one if needed
            if not request.session.session_key:
                request.session.create()
            visitor_id = request.session.session_key or 'unknown'
            try:
                update_website_traffic(visitor_id=visitor_id, request=request)
            except Exception as e:
                logger.error(f"Error updating website traffic: {str(e)}", exc_info=True)
        
        # Continue processing the request
        response = self.get_response(request)
        return response
