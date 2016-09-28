from keystoneauth1.identity import v3
from keystoneauth1 import session


class Session(object):
    def __init__(self, cache, keeper=None):
        """
        Create instance of `Session` class

        @param cahce: Reference to the cache
        @type cache: spamostack.cache.Cache
        @param parent: Parent client for this session
        @type parent: `Client`
        """

        self.user = None
        self.cache = cache
        self.keeper = keeper
        self._session = self.new_session()

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        pass

    @session.deleter
    def session(self):
        del self._session

    def new_session(self):
        """Initiate new session"""

        if self.keeper is not None:
            self.user = self.keeper.get_random("keystone", "users")
            uname = self.user.name
        else:
            uname = "admin"

        auth = v3.Password(auth_url=self.cache["auth_url"],
                           username=uname,
                           password=self.cache["created"]["users"] \
                                    [uname]["password"],
                           project_name=self.cache["created"]["users"] \
                                        [uname]["project_name"],
                           user_domain_id="default",
                           project_domain_id=self.cache["created"] \
                                             ["users"] \
                                             [uname] \
                                             ["project_domain_id"])

        return session.Session(auth=auth)

    def interrupt_session(self):
        """Interrupt old session"""

        if self.session:
            self.user["used"] = False
            self.session = None
