import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

from products.models import Product


@receiver(post_delete, sender=Product)
def delete_product_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
