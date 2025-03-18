import random
import string


def generate_random_slug():
    return "".join(random.choices(string.ascii_letters + string.digits, k=12))
