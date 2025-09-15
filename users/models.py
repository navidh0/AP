from django.contrib.auth.models import AbstractUser, UserManager
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

    # Extra fields
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    ssn = models.CharField(max_length=10, null=True, blank=True)   # ⚠ for real-world use, secure it!
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="male")

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"
