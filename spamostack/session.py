from keystoneauth1.identity import v3
from keystoneauth1 import session

from common import CommonMethods


class Session(CommonMethods, object):
    def __init__(self, cache, parent=None):
        """
        Create instance of `Session` class

        @param cahce: Reference to the cache
        @type cache: spamostack.cache.Cache
        @param parent: Parent client for this session
        @type parent: `Client`
        """

        super(Session, self).__init__()
        self.user = None
        self.cache = cache
        self.parent = parent
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

        self.user = self.get_unused(self.cache["users"])
        auth = v3.Password(auth_url=self.cache["auth_url"],
                           username=self.user.name,
                           password=self.cache["created"]["users"]
                                    [self.user.name]["password"],
                           project_name=self.cache["created"]["users"]
                                        [self.user.name]["project_name"],
                           user_domain_id=self.user.domain_id,
                           project_domain_id=self.cache["created"]["users"]
                                             [self.user.name]
                                             ["project_domain_id"])

        return session.Session(auth=auth)

    def interrupt_session(self):
        """Interrupt old session"""

        if self.session:
            self.user["used"] = False
            self.session = None
