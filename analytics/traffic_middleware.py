from django.utils import timezone
from analytics.signals import update_website_traffic
import logging
import urllib.parse

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
                # Track session start time if not already set
                if 'session_start' not in request.session:
                    request.session['session_start'] = timezone.now().isoformat()
                    request.session.modified = True
                
                # Track referral source for new visitors with validation
                if 'referral_source' not in request.session:
                    referral_source = request.META.get('HTTP_REFERER', '')
                    if referral_source:
                        try:
                            # Validate URL format
                            parsed = urllib.parse.urlparse(referral_source)
                            if parsed.scheme and parsed.netloc:
                                # Check for trusted domains from settings
                                from django.conf import settings
                                if parsed.netloc in settings.TRUSTED_DOMAINS:
                                    request.session['referral_source'] = referral_source[:255]  # Limit length to match model field
                                else:
                                    request.session['referral_source'] = f"untrusted:{referral_source[:247]}"  # Mark as untrusted, limit length
                            else:
                                request.session['referral_source'] = "untrusted:invalid_format"
                            request.session.modified = True
                        except Exception as e:
                            logger.error(f"Error validating referral source: {str(e)}")
                            request.session['referral_source'] = "untrusted:validation_error"
                            request.session.modified = True
                
                update_website_traffic(visitor_id=visitor_id, request=request)
            except Exception as e:
                logger.error(f"Error updating website traffic: {str(e)}", exc_info=True)
        
        # Continue processing the request
        response = self.get_response(request)
        return response
