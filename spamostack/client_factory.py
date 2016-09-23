from session import Session


class ClientFactory(object):
    def __init__(self, cache):
        """
        Create instance of `OSClient` class

        @param cahce: Reference to the cache
        @type cache: spamostack.cache.Cache
        """

        self.cache = cache

    def keystone(self, version="3", active_session=None):
        """
        Create Keystone client

        @param version: Version of the client
        @type version: `str`
        """

        from keystoneclient.client import Client

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Client(version, session=session.session)
        session.parent = client

        return client

    def neutron(self, version="2", active_session=None):
        """
        Create Neutron client

        @param version: Version of the client
        @type version: `str`
        """

        from neutronclient.client import Client

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Client(version, session=session.session)
        session.parent = client

        return client

    def cinder(self, version="3", active_session=None):
        """
        Create Cinder client
        """

        from cinderclient.client import Client

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Client(version, session=session.session)
        session.parent = client

        return client

    def nova(self, version="3", active_session=None):
        """
        Create Nova client
        """

        from novaclient.client import Client

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Client(version, session=session.session)
        session.parent = client

        return client

    def glance(self, version="3", active_session=None):
        """
        Create Glance client
        """

        from glanceclient.client import Client

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Client(version, session=session.session)
        session.parent = client

        return client





