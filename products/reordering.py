import logging
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, StockAlert

logger = logging.getLogger(__name__)

def initiate_reorder(stock_alert):
    """
    Initiate a reorder request for a product when a low stock alert is triggered
    and auto-reorder is enabled.
    
    Args:
        stock_alert (StockAlert): The StockAlert instance triggering the reorder.
    """
    if stock_alert.alert_type != 'product':
        logger.info(f"Reorder not supported for {stock_alert.alert_type} alerts.")
        return
    
    product = stock_alert.product
    if not product.auto_reorder_enabled:
        logger.info(f"Auto-reorder not enabled for product {product.name}.")
        return
    
    if not product.supplier:
        logger.warning(f"No supplier defined for product {product.name}. Cannot initiate reorder.")
        return
    
    supplier = product.supplier
    reorder_quantity = product.reorder_quantity
    
    # Log the reorder attempt
    logger.info(f"Initiating reorder for {product.name} (Quantity: {reorder_quantity}) with supplier {supplier.name}")
    
    # For now, send an email to the supplier contact if available
    if supplier.contact_email:
        subject = f"Reorder Request for {product.name}"
        message = f"""
        Dear {supplier.name},
        
        We would like to place a reorder for the following product:
        
        Product: {product.name}
        Quantity: {reorder_quantity}
        Current Stock: {stock_alert.stock_level}
        
        Please confirm receipt of this request and provide an estimated delivery date.
        
        Regards,
        eStore Inventory Team
        """
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@estore.com')
        recipient_list = [supplier.contact_email]
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            logger.info(f"Reorder email sent to {supplier.name} for {product.name}")
        except Exception as e:
            logger.error(f"Failed to send reorder email to {supplier.name} for {product.name}: {str(e)}")
    else:
        logger.warning(f"No contact email for supplier {supplier.name}. Reorder request logged but not sent.")
    
    # TODO: Implement API integration for automated reordering with supplier systems
    # This could involve making HTTP requests to supplier.api_endpoint with supplier.api_key
    # Example placeholder for future implementation:
    # if supplier.api_endpoint:
    #     send_api_reorder_request(product, reorder_quantity, supplier)
