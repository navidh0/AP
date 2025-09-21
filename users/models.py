from django.core.validators import RegexValidator, EmailValidator, FileExtensionValidator
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static
from django.conf import settings
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("doctor", "Doctor"),
        ("patient", "Patient"),
    ]
    
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
    ]

    # Override AbstractUser fields to change defaults
    first_name = models.CharField(max_length=150, blank=False, null=False)  # make required
    last_name = models.CharField(max_length=150, blank=False, null=False)   # make required
    is_active = models.BooleanField(default=False)  # default True in AbstractUser → we set False

    # Extra Fields 

    avatar = models.ImageField(
        upload_to="avatar/users/", 
        null=True, 
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png"],
                message="Only JPG and PNG image formats are allowed."
            )
        ]
    )

    phone_number = models.CharField(
        max_length=13,  
        unique=True,
        blank=False, 
        null=False,
        validators=[RegexValidator(
            regex=r'^(\+98|0)\d{10}$',
            message="Enter a valid phone number."
        )]
    )

    ssn = models.CharField(
        max_length=10,
        unique=True,
        blank=False, 
        null=False,
        validators=[RegexValidator(
            regex=r'^\d{10}$',
            message="Enter a valid SSN (10 digits)."
        )]
    )
    
    email = models.EmailField(
        unique=True,
        blank=False, 
        null=False,
        validators=[EmailValidator(message="Enter a valid email address.")],
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return static("images/default_user.png")

    def __str__(self):
        return f"{self.username} ({self.role})"


class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expire_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.expire_date >= timezone.now()

    def __str__(self):
        return f"OTP for {self.user.phone_number} - {self.code}"
