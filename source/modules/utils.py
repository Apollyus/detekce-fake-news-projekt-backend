import random
import string

def generate_registration_key(length=12):
    """
    Generuje náhodný registrační klíč požadované délky.
    
    Args:
        length (int): Požadovaná délka klíče (výchozí hodnota je 12 znaků)
        
    Returns:
        str: Vygenerovaný registrační klíč rozdělený pomlčkami po 4 znacích
    """
    # Definice znaků, které mohou být použity v klíči (velká písmena a číslice)
    charset = string.ascii_uppercase + string.digits
    
    # Vytvoření klíče rozdělením na skupiny po 4 znacích oddělené pomlčkami
    return '-'.join(
        ''.join(random.choices(charset, k=4)) for _ in range(length // 4)
    )