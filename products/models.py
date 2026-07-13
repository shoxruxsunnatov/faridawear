from django.db import models

from account.models import (
    User,
    Organization
)

from main.utils import generate_image_filename


class Product(models.Model):
    author = models.ForeignKey(
        User,
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    organization = models.ForeignKey(
        Organization,
        related_name="products",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to=generate_image_filename, blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)

    stock = models.PositiveIntegerField(default=0)
    serial = models.BigIntegerField()

    date_created = models.DateTimeField(auto_now_add=True)

    @property
    def total_base_price(self):
        return self.base_price * self.stock

    @property
    def total_sale_price(self):
        return self.sale_price * self.stock


    class Meta:
        verbose_name_plural = 'Products'
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} | {self.author}"
    
