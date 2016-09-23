import random
import string

from cache import Cache
from client_factory import ClientFactory


class CommonMethods():
    def __init__(self, cache):
        self.cache = cache
        self.client_factory = ClientFactory(self.cache)

    def get_unused(self, name, resource):
        if self.cache[name][resource]['used'] is False:
            self.cache[name][resource]['used'] = True
            return self.cache[name][resource]

    def execute(self, name, func):
        pass

    _ASCII_LETTERS_AND_DIGITS = string.ascii_letters + string.digits

    @staticmethod
    def generate_random_name(prefix="", length=16,
                             choice=_ASCII_LETTERS_AND_DIGITS):
        """Generates pseudo random name.

        :param prefix: str, custom prefix for random name
        :param length: int, length of random name
        :param choice: str, chars for random choice
        :returns: str, pseudo random name
        """

        rand_part = "".join(random.choice(choice) for i in range(length))
        return prefix + rand_part

