from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser

from main.models import Organization, Group

from main.variables import USER_ROLES
from account.utils import (
    generate_username,
    generate_filename
)


class User(AbstractUser):
    photo = models.ImageField(upload_to=generate_filename, blank=True, null=True)
    phone1 = models.CharField(max_length=50, null=True, blank=True)
    phone2 = models.CharField(max_length=50, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=50, choices=USER_ROLES)
    organization = models.ForeignKey(Organization, related_name='users', on_delete=models.CASCADE, blank=True, null=True)
    group = models.ForeignKey(Group, related_name='students', on_delete=models.CASCADE, blank=True, null=True)
    balance = models.FloatField(default=0)
    rating = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):

        if not self.username:
            self.username = generate_username(self, self.get_full_name())

        if len(self.password) < 30:
            self.set_password(self.password)

        super(User, self,).save(*args, **kwargs)
    

    class Meta:
        ordering = ['first_name', 'last_name']
        permissions = [
            ("edit_dictionary", "Edit dictionary"),
            ("view_payment", "View payment"),
            ("edit_payment", "Edit payment"),
        ]

