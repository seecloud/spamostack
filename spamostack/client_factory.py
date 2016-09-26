from session import Session
from keystoneclient.v3.client import Client as KeystoneClient
from resource import Resource


def cache(func):
    def wrapper(self, *args, **kwargs):
        created = func(self, *args, **kwargs)
        self.cache[][created.id] = Resource()


class Keystone(KeystoneClient, object):
    def __init__(self, cache, active_session=None):

        self.cache = cache
        if active_session:
            self.session = active_session
        else:
            self.session = Session(self.cache)

        super(Keystone, self).__init__(session=self.session.session)

        self._users_create = self.users.create
        self.users.create = self.users_create
        self._users_update = self.users.update
        self.users.update = self.users_update
        self._users_delete = self.users.delete
        self.users.delete = self.users_delete

        self._projects_create = self.projects.create
        self.projects.create = self.projects_create
        self._projects_update = self.projects.update
        self.projects.update = self.projects_update
        self._projects_delete = self.projects.delete
        self.projects.delete = self.projects_delete


    @cache
    def users_create(self):
        return self._users_create(self.generate_random_name(),
                                  "default",
                                  self.generate_random_password(),
                                  self.generate_random_email(),
                                  "User with name {}".format(),
                                  True,
                                  self.get_unused("default_project"))

    def users_update(self):
        pass

    def users_delete(self):
        pass

    def projects_create(self):
        pass

    def projects_update(self):
        pass

    def projects_delete(self):
        pass


'''Client.projects.create(self, name, domain, description, enabled, parent)
Client.projects.update(self, project, name, domain, description, enabled)
Client.projects.get(self, project, subtree_as_list, parents_as_list, subtree_as_ids, parents_as_ids)
Client.projects.list(self, domain, user)
Client.projects.delete(self, project)
Client.endpoints.create(self, service, url, interface, region, enabled)
Client.endpoints.update(self, endpoint, service, url, interface, region, enabled)
Client.endpoints.get(self, endpoint)
Client.projects.find(self)
Client.endpoints.list(self, service, interface, region, enabled, region_id)
Client.endpoints.delete(self, endpoint)
Client.users.create(self, name, domain, project, password, email, description, enabled, default_project)
Client.users.update(self, user, name, domain, project, password, email, description, enabled, default_project)
Client.users.get(self, user)
Client.users.list(self, project, domain, group, default_project)
Client.users.delete(self, user)
'''


from neutronclient.v2_0.client import Client as NeutronClient


class Neutron(NeutronClient, object):
    def __init__(self, cache):
        pass


from cinderclient.v3.client import Client as CidnerClient


class Cidner(CidnerClient, object):
    def __init__(self, cache):
        pass


from novaclient.v2.client import Client as NovaClient


class Nova(NovaClient, object):
    def __init__(self, cache):
        pass


from glanceclient.v2.client import Client as GlanceClient


class Glance(GlanceClient, object):
    def __init__(self, cache):
        pass









