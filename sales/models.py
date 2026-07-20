from django.db import models

from account.models import (
    User,
    Organization
)
from products.models import (
    Product
)
from main.variables import (
    PAYMENTS_TYPE_CHOICE
)


class Sale(models.Model):
    author = models.ForeignKey(
        User,
        related_name="sales",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    organization = models.ForeignKey(
        Organization,
        related_name="sales",
        on_delete=models.CASCADE
    )
    base_total = models.DecimalField(max_digits=12, decimal_places=2)
    sale_total = models.DecimalField(max_digits=12, decimal_places=2)
    paid = models.DecimalField(max_digits=12, decimal_places=2)
    debt = models.DecimalField(max_digits=12, decimal_places=2)
    profit = models.DecimalField(max_digits=12, decimal_places=2)

    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Sales'
        ordering = ["-date_created"]

    def __str__(self):
        return f"{self.id} | {self.sale_total}"
    

class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        related_name="items",
        on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        Organization,
        related_name="sale_items",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name="sale_items",
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField()
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)

    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Sales items'
        ordering = ["-date_created"]

    def __str__(self):
        return f"{self.sale.id} | {self.sale_price}"
    

class Payment(models.Model):
    author = models.ForeignKey(
        User,
        related_name="payments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    organization = models.ForeignKey(
        Organization,
        related_name="payments",
        on_delete=models.CASCADE
    )
    sale = models.ForeignKey(
        Sale,
        related_name="payments",
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    profit = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=30, choices=PAYMENTS_TYPE_CHOICE)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Payments'
        ordering = ["-date_created"]

    def __str__(self):
        return f"{self.date_created} | {self.amount} | {self.method}"
    
