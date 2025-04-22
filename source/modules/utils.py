import random
import string

def generate_registration_key(length=12):
    charset = string.ascii_uppercase + string.digits
    return '-'.join(
        ''.join(random.choices(charset, k=4)) for _ in range(length // 4)
    )
