import random
import string


class Keeper(object):
    def __init__(self, cache, session, client_factory):
        """
        Create an instance of `Keeper` class

        @param cahce: Reference to the cache
        @type cache: `spamostack.cache.Cache`
        @param session: Reference to the session
        @type session: `session.Session`
        @param client_factory: Reference to the client factory
        @type client_factory: `client_factory.ClientFactory`
        """

        self.cache = cache
        self.session = session
        self.client_factory = client_factory
        self.default_init()

    def default_init(self):
        """Initialize the default admin user"""

        client = getattr(self.client_factory, "keystone")(self.session)
        user = client.users.find(name="admin")
        self.cache["keystone"]["users"][user.id] = False

    def get_by_id(self, client_name, resource_name, id):
        """
        Get resource by id

        @param client_name: Name of the client
        @type client_name: `str`
        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`
        @param id: ID of the resource
        @type id: `str`
        """

        client = getattr(self.client_factory, client_name)(self.session)
        resource =  getattr(client, resource_name)

        return getattr(resource, "get")(id)

    def get_unused(self, client_name, resource_name):
        """
        Get unused resource

        @param client_name: Name of the client
        @type client_name: `str`
        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`
        """

        for key, value in self.cache[client_name][resource_name]:
            if value is False:
                self.cache[client_name][resource_name][key] = True
                return self.get_by_id(client_name, resource_name, key)

    def get_random(self, client_name, resource_name):
        """
        Get random resource

        @param client_name: Name of the client
        @type client_name: `str`
        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`
        """

        return self.get_by_id(client_name, resource_name,
                              random.choice(self.cache[client_name]
                                            [resource_name].keys()))

    _ASCII_LETTERS_AND_DIGITS = string.ascii_letters + string.digits

    @staticmethod
    def generate_random_name(prefix="", length=16,
                             choice=_ASCII_LETTERS_AND_DIGITS):
        """
        Generates pseudo random name

        @param prefix: Custom prefix for random name
        @type prefix: `str`
        @param length: Length of random name
        @type length: `int`
        @param choice: Chars for random choice
        @type choice: `str`
        @return Pseudo random name `str`
        """

        rand_part = "".join(random.choice(choice) for i in range(length))
        return prefix + rand_part

    @staticmethod
    def generate_random_password():
        """Generate pseudo random password"""

        return Keeper.generate_random_name()

    @staticmethod
    def generate_random_email():
        """Generate pseudo random email"""

        user = Keeper.generate_random_name(length=3,
                                           choice=string.ascii_lowercase)
        sld = Keeper.generate_random_name(length=3,
                                          choice=string.ascii_lowercase)
        tld = Keeper.generate_random_name(length=3,
                                          choice=string.ascii_lowercase)
        
        return "{0}@{1}.{2}".format(user, sld, tld)
