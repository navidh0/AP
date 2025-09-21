import random, datetime
from django.utils import timezone
from django.conf import settings
from users.models import OTP


def generate_otp():
    return str(random.randint(100000, 999999))


def create_otp(user):
    code = generate_otp()
    expires_at = timezone.now() + datetime.timedelta(minutes=2)  # valid 2 mins
    return OTP.objects.create(user=user, code=code, expire_date=expires_at)


def send_otp(phone_number, code):
    print(f"[DEV MODE] OTP for {phone_number}: {code}")


def verify_otp(user, code):
    otp = OTP.objects.filter(user=user, code=code).order_by("-created_at").first()
    if otp and otp.is_valid():
        return True
    return False
