from django.core.management.base import BaseCommand
from core.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a test notification'

    def handle(self, *args, **options):
        # Get the first user
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found in database"))
            return

        self.stdout.write(f"Creating notification for user: {user.username}")
        
        # Create a test notification
        notification = Notification.create_notification(
            user=user,
            notification_type='appointment_cancelled',
            title='Test Notification',
            message='This is a test notification to verify the system works.',
            appointment=None
        )
        
        self.stdout.write(self.style.SUCCESS(f"Notification created with ID: {notification.id}"))
        self.stdout.write(f"Total notifications for user: {Notification.objects.filter(user=user).count()}")
        
        # List all notifications for this user
        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        self.stdout.write(f"\nAll notifications for {user.username}:")
        for notif in notifications:
            self.stdout.write(f"  - {notif.title} ({notif.notification_type}) - {'Read' if notif.is_read else 'Unread'}")
