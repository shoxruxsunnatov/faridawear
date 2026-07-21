import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from products.models import Product


@receiver(post_delete, sender=Product)
def delete_product_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(pre_save, sender=Product)
def delete_old_product_image(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = Product.objects.get(pk=instance.pk)
    except Product.DoesNotExist:
        return

    old_image = old_instance.image
    new_image = instance.image

    if old_image and old_image != new_image:
        if os.path.isfile(old_image.path):
            os.remove(old_image.path)
