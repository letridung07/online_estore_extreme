from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Max
from django.utils import timezone
from datetime import timedelta
from analytics.models import UserSegment
from orders.models import Order
import logging

class Command(BaseCommand):
    help = 'Update user segments based on their behavior and activity'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        self.stdout.write(self.style.SUCCESS('Starting user segment updates...'))
        
        # Get all active users
        users = User.objects.filter(is_active=True)
        total_users = len(users)
        processed = 0
        
        # Time thresholds for activity analysis
        recent_threshold = timezone.now() - timedelta(days=30)
        long_term_threshold = timezone.now() - timedelta(days=180)
        
        for user in users:
            try:
                # Get user's order data for segmentation
                orders = Order.objects.filter(user=user)
                order_count = orders.count()
                recent_orders = orders.filter(created_at__gte=recent_threshold).count()
                avg_order_value = orders.aggregate(Avg('total_price'))['total_price__avg'] or 0.00
                last_activity = orders.aggregate(Max('created_at'))['created_at__max']
                
                # Calculate purchase frequency (orders per month over the last 6 months)
                if order_count > 0:
                    long_term_orders = orders.filter(created_at__gte=long_term_threshold).count()
                    purchase_frequency = long_term_orders / 6.0  # Average per month over 6 months
                else:
                    purchase_frequency = 0.0
                
                # Determine segment based on behavior
                if order_count == 0:
                    segment_type = 'new'
                elif recent_orders == 0 and last_activity and last_activity < recent_threshold:
                    segment_type = 'inactive'
                elif purchase_frequency >= 2.0:
                    segment_type = 'frequent_buyer'
                elif avg_order_value >= 100.00:  # Threshold for high spender
                    segment_type = 'high_spender'
                else:
                    segment_type = 'budget_conscious'
                
                # Update or create UserSegment
                UserSegment.objects.update_or_create(
                    user=user,
                    defaults={
                        'segment_type': segment_type,
                        'purchase_frequency': purchase_frequency,
                        'average_order_value': avg_order_value,
                        'last_activity': last_activity
                    }
                )
                self.stdout.write(f'Updated segment for user {user.username} to {segment_type}')
                
            except Exception as e:
                logger.error(f'Error updating segment for user {user.username}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'Error for user {user.username}: {str(e)}'))
            
            processed += 1
            if processed % 10 == 0:
                self.stdout.write(f'Processed {processed}/{total_users} users...')
        
        self.stdout.write(self.style.SUCCESS(f'Finished updating segments for {total_users} users.'))
