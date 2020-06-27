from string import ascii_letters, digits, punctuation
from random import choices
from time import time

def get_random_string():
    superset = ascii_letters + digits + punctuation
    initial_string = ''.join(choices(superset, k=32))
    unix_time = hex(int(time()))
    return initial_string + unix_time