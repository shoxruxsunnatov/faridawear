import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

from dictionary.models import Vocabulary


@receiver(post_delete, sender=Vocabulary)
def delete_vocab_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
