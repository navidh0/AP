from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, EmailValidator, FileExtensionValidator
from django.templatetags.static import static
from django.db import models


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

    # Override AbstractUser defaults → make required
    first_name = models.CharField(max_length=150, blank=False, null=False)
    last_name = models.CharField(max_length=150, blank=False, null=False)

    #Extra Fields 
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")
    
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
    
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return static("images/default_user.png")

    def __str__(self):
        return f"{self.username} ({self.role})"
