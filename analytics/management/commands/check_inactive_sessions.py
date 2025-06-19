from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
import json
from datetime import timedelta
import re

DATE_FORMAT = "%Y-%m-%d"

class Command(BaseCommand):
    help = 'Checks for inactive sessions with single page visits and adjusts bounce counts accordingly.'

    def adjust_bounce_count(self, session, session_data, visited_pages_key, visited_pages_value, date):
        """
        Adjusts the bounce count for a session and marks it as processed.
        
        Args:
            session: The Session object to update.
            session_data: The decoded session data dictionary.
            visited_pages_key: The key in session_data for visited pages.
            visited_pages_value: The value associated with visited_pages_key (list of pages).
            date: The date object to use for the cache key.
        
        Returns:
            bool: True if bounce count was adjusted, False otherwise.
        """
        bounces_key = f"website_traffic_bounces_{date}"
        # Increment bounce count to track sessions with only one page visit 
        # that have been inactive for over 30 minutes, indicating a bounce in website traffic analytics.
        cache.incr(bounces_key)
        # Mark session as processed by updating the visited_pages data
        session_data[visited_pages_key] = visited_pages_value + ["processed_bounce"]
        session.session_data = SessionStore().encode(session_data)
        session.save()
        return True

    def handle(self, *args, **options):
        """
        Scan for sessions that have only one page visit and have been inactive for over 30 minutes.
        Increment bounce counts for these sessions and mark them as processed to avoid double-counting.
        Only process sessions that haven't been checked recently based on a last_checked timestamp.
        """
        self.stdout.write("Starting check for inactive sessions...")
        inactivity_threshold = timezone.now() - timedelta(minutes=30)
        recheck_threshold = timezone.now() - timedelta(hours=1)  # Re-check sessions only after 1 hour
        sessions_processed = 0
        bounces_adjusted = 0

        # Get all sessions that are still active in the database, processing in batches
        for session in Session.objects.filter(expire_date__gte=timezone.now()).iterator(chunk_size=1000):
            try:
                session_data = session.get_decoded()
                # Check if the session has been checked recently
                last_checked_str = session_data.get('last_checked')
                if last_checked_str:
                    try:
                        last_checked = timezone.datetime.fromisoformat(last_checked_str)
                        if last_checked > recheck_threshold:
                            continue  # Skip sessions checked within the last hour
                    except ValueError:
                        self.stderr.write(f"Invalid last_checked format for session {session.session_key}")
                        # Process the session if the format is invalid, to be safe

                # Look for keys that match the visited_pages pattern
                for key, value in session_data.items():
                    if key.startswith("visited_pages_"):
                        # Extract date from the key if possible, format is visited_pages_{visitor_id}_{date}
                        try:
                            match = re.search(r'\d{4}-\d{2}-\d{2}$', key)
                            if match:
                                date_str = match.group(0)
                                date = timezone.datetime.strptime(date_str, DATE_FORMAT).date()
                            else:
                                date = timezone.now().date()
                        except (IndexError, ValueError):
                            date = timezone.now().date()

                        # Check if only one page was visited
                        if isinstance(value, list) and len(value) == 1:
                            # Check if the session has been inactive using the last_activity timestamp
                            last_activity_str = session_data.get('last_activity')
                            if last_activity_str:
                                try:
                                    last_activity = timezone.datetime.fromisoformat(last_activity_str)
                                    if last_activity < inactivity_threshold:
                                        if self.adjust_bounce_count(session, session_data, key, value, date):
                                            bounces_adjusted += 1
                                            sessions_processed += 1
                                except ValueError:
                                    self.stderr.write(f"Invalid last_activity format for session {session.session_key}")
                                    # Fallback to expire_date for older sessions or format errors
                                    if session.expire_date < inactivity_threshold:
                                        if self.adjust_bounce_count(session, session_data, key, value, date):
                                            bounces_adjusted += 1
                                            sessions_processed += 1
                            else:
                                # Fallback for sessions without last_activity timestamp
                                if session.expire_date < inactivity_threshold:
                                    if self.adjust_bounce_count(session, session_data, key, value, date):
                                        bounces_adjusted += 1
                                        sessions_processed += 1
                # Update last_checked timestamp for this session
                session_data['last_checked'] = timezone.now().isoformat()
                session.session_data = SessionStore().encode(session_data)
                session.save()
            except Exception as e:
                self.stderr.write(f"Error processing session {session.session_key}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(
            f"Completed check. Processed {sessions_processed} sessions, adjusted {bounces_adjusted} bounce counts."
        ))
