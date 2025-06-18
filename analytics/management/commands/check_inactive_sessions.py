from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from django.contrib.sessions.models import Session
import json
from datetime import timedelta

DATE_FORMAT = "%Y-%m-%d"

class Command(BaseCommand):
    help = 'Checks for inactive sessions with single page visits and adjusts bounce counts accordingly.'

    def handle(self, *args, **options):
        """
        Scan for sessions that have only one page visit and have been inactive for over 30 minutes.
        Increment bounce counts for these sessions and mark them as processed to avoid double-counting.
        """
        self.stdout.write("Starting check for inactive sessions...")
        inactivity_threshold = timezone.now() - timedelta(minutes=30)
        sessions_processed = 0
        bounces_adjusted = 0

        # Get all sessions that are still active in the database
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            try:
                session_data = session.get_decoded()
                # Look for keys that match the visited_pages pattern
                for key, value in session_data.items():
                    if key.startswith("visited_pages_"):
                        # Extract date from the key if possible, format is visited_pages_{visitor_id}_{date}
                        try:
                            date_str = key.split("_")[-1]
                            date = timezone.datetime.strptime(date_str, DATE_FORMAT).date()
                        except (IndexError, ValueError):
                            date = timezone.now().date()

                        # Check if only one page was visited
                        if isinstance(value, list) and len(value) == 1:
                            # Check if the session has been inactive (using last modification or creation as proxy)
                            # Since Django doesn't store last access time by default, we might need a custom way to track this
                            # For now, assume session creation or last update as the activity time (limitation)
                            if session.expire_date < inactivity_threshold:
                                bounces_key = f"website_traffic_bounces_{date}"
                                cache.incr(bounces_key)
                                bounces_adjusted += 1
                                # Mark session as processed by clearing or updating the visited_pages data
                                session_data[key] = value + ["processed_bounce"]
                                session.session_data = Session.objects.encode(session_data)
                                session.save()
                                sessions_processed += 1
            except Exception as e:
                self.stderr.write(f"Error processing session {session.session_key}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(
            f"Completed check. Processed {sessions_processed} sessions, adjusted {bounces_adjusted} bounce counts."
        ))
