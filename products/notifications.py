from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import StockAlert

def send_low_stock_notification(stock_alert):
    """
    Send an email notification to admin users when a low stock alert is created.
    
    Args:
        stock_alert (StockAlert): The StockAlert instance triggering the notification.
    """
    # Get admin users (superusers or staff)
    admin_users = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
    admin_emails = [user.email for user in admin_users if user.email]
    
    if not admin_emails:
        # Log or handle the case where no admin emails are available
        logger = logging.getLogger(__name__)
        logger.warning("No admin emails found for low stock notification.")
        return
    
    # Determine the item name based on alert type
    if stock_alert.alert_type == 'product':
        item_name = stock_alert.product.name
        item_type = 'Product'
    else:
        item_name = f"{stock_alert.variant.product.name} - {stock_alert.variant.name}"
        item_type = 'Variant'
    
    # Construct email content
    subject = f"Low Stock Alert: {item_name}"
    message = f"""
    Dear Admin,
    
    A low stock alert has been triggered for the following item:
    
    Type: {item_type}
    Name: {item_name}
    Current Stock: {stock_alert.stock_level}
    Alert Date: {stock_alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
    
    Please review the inventory and take necessary action to restock this item.
    You can manage this alert in the Django Admin interface under Stock Alerts.
    
    Regards,
    eStore Inventory System
    """
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@estore.com')
    recipient_list = admin_emails
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        print(f"Low stock notification sent for {item_name} to {len(admin_emails)} admin(s).")
    except Exception as e:
        print(f"Failed to send low stock notification for {item_name}: {str(e)}")
