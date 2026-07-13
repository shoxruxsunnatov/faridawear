from django.apps import AppConfig


class DictionaryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dictionary'


    def ready(self):
        from dictionary.signals import delete_vocab_image_file