from django.core.management.base import BaseCommand
from core.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Test notification system'

    def handle(self, *args, **options):
        self.stdout.write("=== NOTIFICATION SYSTEM TEST ===")
        self.stdout.write(f"Total notifications in database: {Notification.objects.count()}")
        self.stdout.write(f"Total users in database: {User.objects.count()}")

        # Check notifications for each user
        for user in User.objects.all():
            user_notifications = Notification.objects.filter(user=user)
            self.stdout.write(f"\nUser: {user.username} ({user.get_full_name()})")
            self.stdout.write(f"  Notifications: {user_notifications.count()}")
            self.stdout.write(f"  Unread: {user_notifications.filter(is_read=False).count()}")
            
            for notification in user_notifications[:3]:  # Show first 3
                self.stdout.write(f"    - {notification.title} ({notification.notification_type}) - {'Read' if notification.is_read else 'Unread'}")

        self.stdout.write("\n=== TEST COMPLETE ===")
