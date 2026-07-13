import uuid
from random import randint


def get_clean_text(text):
    allowed_chars = 'qwertyuiopasdfghjklzxcvbnm'
    allowed_chars += allowed_chars.upper()

    clean_text = ''
    for char in text:
        if char in allowed_chars:
            clean_text += char
    
    return clean_text.lower()


def generate_username(user_model, full_name):
    username = f'{full_name}{randint(1000, 9999)}'
    while user_model.objects.filter(username=username).first():
        username = f'{full_name}{randint(1000, 9999)}'

    return username


def generate_password():
    return str(randint(10000000, 99999999))


def generate_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'photos/{uuid.uuid4()}.{ext}'
    return filename
