import uuid
from random import randint


def get_random_index() -> int:
    return randint(1, 100)


def generate_image_filename(instance, filename) -> str:
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'images/{filename}'
