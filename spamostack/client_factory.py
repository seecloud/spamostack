from session import Session
from resource import Resource
from common import CommonMethods

import inspect

from keystoneclient.v3.client import Client as KeystoneClient
from neutronclient.v2_0.client import Client as NeutronClient
from cinderclient.v3.client import Client as CidnerClient
from novaclient.v2.client import Client as NovaClient
from glanceclient.v2.client import Client as GlanceClient


def get_class(func):
    for cls in inspect.getmro(func.im_class):
        if func.__name__ in cls.__dict__:
            return cls
    return None

def cache(func):
    def wrapper(self, *args, **kwargs):
        processed = func(self, *args, **kwargs)
        section = ""

        if "user" in func.__name__:
            section = "users"
        elif "project" in func.__name__:
            section = "projects"
        self.cache[get_class(func).__name__.lower()][section][processed.id].\
            setdefault(False)

        return processed

    return wrapper

def uncache(func):
    def wrapper(self, *args, **kwargs):
        obj = kwargs[kwargs.keys()[0]]
        processed = func(self, *args, **kwargs)
        section = ""

        if "user" in func.__name__:
            section = "users"
        elif "project" in func.__name__:
            section = "projects"
        del self.cache[get_class(func).__name__.lower()][section][processed.id]

        return processed

    return wrapper


class ClientFactory(object):
    def __init__(self, cache):
        """
        Create instance of `ClientFactory` class
        @param cahce: Reference to the cache
        @type cache: spamostack.cache.Cache
        """

        self.cache = cache

    def keystone(self, active_session=None):
        """
        Create Keystone client
        @param version: Version of the client
        @type version: `str`
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Keystone(self.cache, session=session)
        session.parent = client

        return client

    def neutron(self, active_session=None):
        """
        Create Neutron client
        @param version: Version of the client
        @type version: `str`
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Neutron(self.cache, session=session)
        session.parent = client

        return client

    def cinder(self, active_session=None):
        """
        Create Cinder client
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Cinder(self.cache, session=session)
        session.parent = client

        return client

    def nova(self, active_session=None):
        """
        Create Nova client
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Nova(self.cache, session=session)
        session.parent = client

        return client

    def glance(self, active_session=None):
        """
        Create Glance client
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache)

        client = Glance(self.cache, session=session)
        session.parent = client

        return client


class Keystone(KeystoneClient, CommonMethods, object):
    def __init__(self, cache, active_session=None):
        """
        Create `Keystone` class instance.

        @param cache: Cache
        @type cache: `cache.Cache`
        @param active_session: Specific session for that client
        @type active_session: `session.Session`
        """

        self.cache = cache
        if active_session:
            self.session = active_session
        else:
            self.session = Session(self.cache)

        super(Keystone, self).__init__(session=self.session.session)

        self._users_create = self.users.create
        self.users.create = self.user_create
        self._users_update = self.users.update
        self.users.update = self.user_update
        self._users_delete = self.users.delete
        self.users.delete = self.user_delete

        self._projects_create = self.projects.create
        self.projects.create = self.project_create
        self._projects_update = self.projects.update
        self.projects.update = self.project_update
        self._projects_delete = self.projects.delete
        self.projects.delete = self.project_delete

    @cache
    def user_create(self):
        name = self.generate_random_name()
        password = self.generate_random_password()
        project = self.get_random(self.cache["keystone"]["projects"])
        user = self._users_create(name=name,
                                  domain="default",
                                  password=password,
                                  email=self.generate_random_email(),
                                  description="User with name {}".format(name),
                                  enabled=True,
                                  default_project=project)

        self.roles.grant(self.roles.find(name="admin"), user, project=project)
        self.cache["created"]["users"][name]["password"] = password
        self.cache["created"]["users"][name]["project_name"] = project.name
        self.cache["created"]["users"][name]["project_domain_id"] = \
            project.domain_id

        return user

    @cache
    def user_update(self):
        name = self.generate_random_name()
        return self._users_update(user=self.get_random(self.cache
                                                       ["keystone"]
                                                       ["users"]),
                                  name=name,
                                  domain="default",
                                  password=self.generate_random_password(),
                                  email=self.generate_random_email(),
                                  description="User with name {}".format(name),
                                  enabled=True)

    @uncache
    def user_delete(self):
        return self._users_delete(self.get_random(self.cache["keystone"]
                                                  ["users"]))

    @cache
    def project_create(self):
        name = self.generate_random_name()
        return self._projects_create(name=name,
                                     domain="default",
                                     description="Project {}".format(name),
                                     enabled=True)

    @cache
    def project_update(self):
        name = self.generate_random_name()
        return self._projects_update(project=self.get_random(self.cache
                                                             ["keystone"]
                                                             ["projects"]),
                                     name=name,
                                     domain="default",
                                     description="Project {}".format(name),
                                     enabled=True)

    @uncache
    def project_delete(self):
        return self._projects_delete(self.get_random(self.cache["keystone"]
                                                     ["projects"]))


class Neutron(NeutronClient, object):
    def __init__(self, cache):
        pass


class Cinder(CinderClient, object):
    def __init__(self, cache):
        pass


class Nova(NovaClient, object):
    def __init__(self, cache):
        pass


class Glance(GlanceClient, object):
    def __init__(self, cache):
        pass
