from django.db import models

from account.models import User, Organization
from main.models import Group

from main.variables import TRANSACTION_TYPE_CHOICE


class Transaction(models.Model):
    user = models.ForeignKey(User, related_name="transactions", on_delete=models.CASCADE)
    amount = models.FloatField()
    category = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICE)
    group = models.ForeignKey(Group, related_name='transactions', on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(Organization, related_name='transactions', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="transactions_created", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date_created']
    
    def __str__(self):
        return f"{self.user.get_full_name()} | {self.category} {self.amount}"
    