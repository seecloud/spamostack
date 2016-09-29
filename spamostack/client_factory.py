#
# Copyright 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import cinderclient.v3.client as cinder_client
import glanceclient.v2.client as glance_client
import keystoneclient.v3.client as keystone_client
import neutronclient.v2_0.client as neutron_client
import novaclient.v2.client as nova_client
from session import Session


def cache(func):
    def wrapper(self, *args, **kwargs):
        processed = func(self, *args, **kwargs)
        section = ""

        if "user" in func.__name__:
            section = "users"
        elif "project" in func.__name__:
            section = "projects"
        (self.cache[self.__class__.__name__.lower()][section].
         setdefault(processed.id, False))

        return processed

    return wrapper


def uncache(func):
    def wrapper(self, *args, **kwargs):
        processed = func(self, *args, **kwargs)
        section = ""

        if "user" in func.__name__:
            section = "users"
        elif "project" in func.__name__:
            section = "projects"
        del self.cache[self.__class__.__name__.lower()][section][processed.id]

        return processed

    return wrapper


class ClientFactory(object):
    def __init__(self, cache, keeper=None):
        """Create instance of `ClientFactory` class

        @param cahce: Reference to the cache
        @type cache: spamostack.cache.Cache
        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        self.cache = cache
        self.keeper = keeper

    def keystone(self, active_session=None):
        """Create Keystone client

        @param active_session: Active session instead of creating new one
        @type active_session: `session.Session`
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache, self.keeper)

        client = Keystone(self.cache, self.keeper, active_session=session)

        return client

    def neutron(self, active_session=None):
        """Create Neutron client

        @param active_session: Active session instead of creating new one
        @type active_session: `session.Session`
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache, self.keeper)

        client = Neutron(self.cache, self.keeper, active_session=session)

        return client

    def cinder(self, active_session=None):
        """Create Cinder client

        @param active_session: Active session instead of creating new one
        @type active_session: `session.Session`
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache, self.keeper)

        client = Cinder(self.cache, self.keeper, active_session=session)

        return client

    def nova(self, active_session=None):
        """Create Nova client

        @param active_session: Active session instead of creating new one
        @type active_session: `session.Session`
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache, self.keeper)

        client = Nova(self.cache, self.keeper, active_session=session)

        return client

    def glance(self, active_session=None):
        """Create Glance client

        @param active_session: Active session instead of creating new one
        @type active_session: `session.Session`
        """

        if active_session is not None:
            session = active_session
        else:
            session = Session(self.cache, self.keeper)

        client = Glance(self.cache, self.keeper, active_session=session)

        return client


class Keystone(keystone_client.Client, object):
    def __init__(self, cache, keeper=None, active_session=None):
        """Create `Keystone` class instance.

        @param cache: Cache
        @type cache: `cache.Cache`
        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        @param active_session: Specific session for that client
        @type active_session: `session.Session`
        """

        self.cache = cache
        self.keeper = keeper
        if active_session:
            self.session = active_session
        else:
            self.session = Session(self.cache, self.keeper)

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
        name = self.keeper.generate_random_name()
        password = self.keeper.generate_random_password()
        project = self.keeper.get_random("keystone", "projects")
        user = self._users_create(name=name,
                                  domain="default",
                                  password=password,
                                  email=self.keeper.generate_random_email(),
                                  description="User with name {}".format(name),
                                  enabled=True,
                                  default_project=project)

        self.roles.grant(self.roles.find(name="admin"), user, project=project)
        self.cache["created"]["users"][name]["password"] = password
        self.cache["created"]["users"][name]["project_name"] = project.name
        (self.cache["created"]["users"][name]
         ["project_domain_id"]) = project.domain_id

        return user

    @cache
    def user_update(self):
        name = self.keeper.generate_random_name()
        user = None
        while user is None or user.name == "admin":
            user = self.keeper.get_random("keystone", "users")
        return self._users_update(user=user,
                                  name=name,
                                  domain="default",
                                  password=(self.keeper.
                                            generate_random_password()),
                                  email=self.keeper.generate_random_email(),
                                  description="User with name {}".format(name),
                                  enabled=True)

    @uncache
    def user_delete(self):
        return self._users_delete(self.keeper.get_random("keystone", "users"))

    @cache
    def project_create(self):
        name = self.keeper.generate_random_name()
        return self._projects_create(name=name,
                                     domain="default",
                                     description="Project {}".format(name),
                                     enabled=True)

    @cache
    def project_update(self):
        name = self.keeper.generate_random_name()
        project = None
        while project is None or project.name == "admin":
            project = self.keeper.get_random("keystone", "projects")
        return self._projects_update(project=project,
                                     name=name,
                                     domain="default",
                                     description="Project {}".format(name),
                                     enabled=True)

    @uncache
    def project_delete(self):
        return self._projects_delete(self.keeper.get_random("keystone",
                                                            "projects"))


class Neutron(neutron_client.Client, object):
    def __init__(self, cache):
        pass


class Cinder(cinder_client.Client, object):
    def __init__(self, cache):
        pass


class Nova(nova_client.Client, object):
    def __init__(self, cache):
        pass


class Glance(glance_client.Client, object):
    def __init__(self, cache):
        pass
