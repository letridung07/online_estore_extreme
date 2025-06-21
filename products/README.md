# Products App - Inventory Management Features

This document provides an overview and usage guide for the inventory management features implemented in the Products app of the eStore platform. These features are designed to help manage stock levels, alert administrators to low stock situations, and facilitate automated reordering with suppliers.

## Table of Contents
- [Overview](#overview)
- [Low Stock Alerts](#low-stock-alerts)
- [Configuration](#configuration)
- [Periodic Stock Checks](#periodic-stock-checks)
- [Automated Reordering](#automated-reordering)
- [Admin Interface](#admin-interface)

## Overview
The inventory management system enhances the eStore platform by providing tools to monitor and manage product stock levels effectively. Key features include:
- **Low Stock Alerts**: Automatic detection and notification when stock levels fall below a defined threshold.
- **Periodic Stock Checks**: A management command to ensure no low-stock items are missed.
- **Automated Reordering**: Groundwork for automatic reorder requests with suppliers when stock is low.
- **Admin Interface Enhancements**: Tools in the Django admin interface to manage inventory settings and alerts.

## Low Stock Alerts
Low stock alerts are triggered when the stock level of a Product or Variant falls below its defined `low_stock_threshold`. Alerts are managed through the `StockAlert` model and notifications are sent to administrators.

### How It Works
- **Threshold Definition**: Each Product and Variant has a `low_stock_threshold` field (default set to 5 units) that defines the stock level at which an alert is triggered.
- **Signal-Based Detection**: Django signals (`post_save`) on Product and Variant models check stock levels after any update. If stock is below the threshold and no recent pending alert exists, a new `StockAlert` record is created.
- **Notifications**: Upon creation of a `StockAlert`, an email notification is sent to admin users (superusers or staff) or to emails defined in `INVENTORY_NOTIFICATION_EMAILS` in settings.py.

### Managing Alerts
- Alerts can be viewed and managed in the Django admin interface under "Stock Alerts".
- Administrators can mark alerts as resolved individually or in bulk using the "Mark selected alerts as resolved" action.

## Configuration
Inventory management settings are defined in `estore/settings.py` under "Inventory Management Settings". Customize these settings to fit your operational needs:

- **`DEFAULT_LOW_STOCK_THRESHOLD`**: Default threshold for low stock alerts if not specified per product (default: 5).
- **`INVENTORY_NOTIFICATION_EMAILS`**: List of email addresses to receive low stock notifications. If empty, notifications are sent to admin users with email addresses (superusers and staff).
- **`INVENTORY_NOTIFICATION_FREQUENCY`**: Hours between repeated notifications for the same item to prevent spam (default: 24 hours).
- **`AUTO_REORDER_ENABLED_GLOBALLY`**: Global toggle to enable or disable auto-reordering functionality across the platform (default: False).

### Email Configuration
Ensure that Django's email settings are configured correctly for notifications to work:
- Set `DEFAULT_FROM_EMAIL` in settings.py for the sender address of notification emails.
- Configure SMTP or other email backend settings as per Django documentation.

## Periodic Stock Checks
To ensure no low-stock items are missed due to updates outside the application or signal failures, a management command is provided for periodic stock checks.

### Running the Command
Run the following command to check stock levels for all products and variants:
```bash
python manage.py check_stock_levels
```
- This command iterates through all Products and Variants, creating `StockAlert` records for items below their threshold if no pending alert exists.
- Notifications are sent for new alerts created during this check.

### Scheduling
Schedule this command to run periodically using a cron job or a task scheduler like Celery with django-celery-beat for automated checks. Example cron job for daily execution at midnight:
```bash
0 0 * * * python /path/to/your/project/manage.py check_stock_levels
```

## Automated Reordering
The system lays the groundwork for automated reordering with suppliers when low stock alerts are triggered for products with auto-reorder enabled.

### Setup
- **Supplier Model**: Define supplier information including name, contact email, phone number, API endpoint, and API key in the `Supplier` model via the admin interface.
- **Product Settings**: For each product, set a `supplier`, `reorder_quantity` (default amount to reorder), and enable `auto_reorder_enabled` in the product admin page.
- **Global Toggle**: Ensure `AUTO_REORDER_ENABLED_GLOBALLY` is set to `True` in settings.py to activate this feature across the platform.

### How It Works
- When a `StockAlert` is created for a product and `auto_reorder_enabled` is True, the system initiates a reorder request.
- Currently, the reorder process sends an email to the supplier's contact email (if available) requesting the defined `reorder_quantity`.
- Logs are created for all reorder attempts, which can be viewed in the application logs for debugging and tracking.

### Future Enhancements
- The `api_endpoint` and `api_key` fields in the Supplier model are placeholders for future API integration. You can extend the `initiate_reorder` function in `products/reordering.py` to make HTTP requests to supplier systems for direct automated ordering.

## Admin Interface
The Django admin interface has been enhanced to support inventory management:
- **Product Admin**: Includes fields for `stock`, `low_stock_threshold`, `supplier`, `reorder_quantity`, and `auto_reorder_enabled` under an "Inventory" fieldset. A column for `auto_reorder_enabled` is added to the list view.
- **Variant Admin**: Displays a `low_stock_status` boolean indicator in the list view for quick identification of low stock items.
- **StockAlert Admin**: Lists all alerts with filters for type, status, and creation date. Includes a custom action to mark alerts as resolved.
- **Supplier Admin**: Manage supplier information with fields for contact details and API settings for future integration.

### Usage Tips
- Use the `low_stock_status` column in Product and Variant lists to quickly identify items needing attention.
- Filter Stock Alerts by `status='pending'` to focus on unresolved issues.
- Set up suppliers first before assigning them to products for reordering.

## Troubleshooting
- **Notifications Not Sending**: Check email configuration in settings.py and ensure admin users have valid email addresses or that `INVENTORY_NOTIFICATION_EMAILS` is populated.
- **Alerts Not Triggering**: Verify that signals are connected in `products/apps.py` and that stock updates are being saved correctly. Run `python manage.py check_stock_levels` manually to test alert creation.
- **Reorder Emails Not Sending**: Ensure suppliers have valid contact emails and that `auto_reorder_enabled` is set for relevant products. Check logs for errors related to email sending.

For further assistance or to report issues, contact the development team or refer to Django documentation for email and signal configurations.
