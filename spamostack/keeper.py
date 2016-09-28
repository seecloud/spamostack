import random
import string


class Keeper(object):
    def __init__(self, cache, session, client_factory):
        self.cache = cache
        self.session = session
        self.client_factory = client_factory
        self.default_init()

    def default_init(self):
        client = getattr(self.client_factory, "keystone")(self.session)
        user = client.users.find(name="admin")
        self.cache["keystone"]["users"][user.id] = False

    def get_by_id(self, client_name, resource_name, id):
        client = getattr(self.client_factory, client_name)(self.session)
        resource =  getattr(client, resource_name)

        return getattr(resource, "get")(id)

    def get_unused(self, client_name, resource_name):
        for key, value in self.cache[client_name][resource_name]:
            if value is False:
                self.cache[client_name][resource_name][key] = True
                return self.get_by_id(client_name, resource_name, key)

    def get_random(self, client_name, resource_name):
        return self.get_by_id(client_name, resource_name,
                              random.choice(self.cache[client_name]
                                            [resource_name].values()))

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

    @staticmethod
    def generate_random_password():
        return Keeper.generate_random_name()

    @staticmethod
    def generate_random_email():
        user = Keeper.generate_random_name(length=3,
                                           choice=string.ascii_lowercase)
        sld = Keeper.generate_random_name(length=3,
                                          choice=string.ascii_lowercase)
        tld = Keeper.generate_random_name(length=3,
                                          choice=string.ascii_lowercase)
        
        return "{0}@{1}.{2}".format(user, slt, tld)
