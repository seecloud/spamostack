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

import faker

import argparse
from openstackclient.common import clientmanager
from os_client_config import config as cloud_config

import copy


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
    def __init__(self, cache, user, keeper=None):
        """Create instance of `ClientFactory` class

        @param cahce: Reference to the cache
        @type cache: spamostack.cache.Cache
        @param user: User for client factory instance
        @type user: `dict` or `User`
        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        self.cache = cache
        self.keeper = keeper
        self.faker = faker.Factory.create('en_US')

        # Initialization of client manager
        if isinstance(user, dict):
            user_copy = user.copy()
            user_copy.update(self.cache["api"])
            opts = argparse.Namespace(**user_copy)
        else:
            user_copy = self.cache["users"][user.name].copy()
            user_copy.update(self.cache["api"])
            opts = argparse.Namespace(**user_copy)
        opts.cloud = ""
        cc = cloud_config.OpenStackConfig()
        cloud = cc.get_one_cloud(cloud=opts.cloud, argparse=opts)
        api_version = {}
        for mod in clientmanager.PLUGIN_MODULES:
            version_opt = getattr(opts, mod.API_VERSION_OPTION, None)
            if version_opt:
                api = mod.API_NAME
                api_version[api] = version_opt

        self.client_manager = clientmanager.ClientManager(
            cli_options=cloud, api_version=api_version)
        self.client_manager.setup_auth()
        self.client_manager.auth_ref

    def keystone(self):
        """Create Keystone client."""

        return Keystone(self.cache, self.client_manager.identity, self.faker,
                        self.keeper)

    def neutron(self):
        """Create Neutron client."""

        return Neutron(self.cache, self.client_manager.network, self.faker,
                       self.keeper)

    def cinder(self):
        """Create Cinder client."""

        return Cinder(self.cache, self.client_manager.volume, self.faker,
                      self.keeper)

    def nova(self):
        """Create Nova client."""

        return Nova(self.cache, self.client_manager.compute, self.faker,
                    self.keeper)

    def glance(self):
        """Create Glance client."""

        return Glance(self.cache, self.client_manager.image, self.faker,
                      self.keeper)


class Keystone(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `Keystone` class instance.

        @param cache: Cache
        @type cache: `cache.Cache`
        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        @param active_session: Specific session for that client
        @type active_session: `session.Session`
        """

        self.cache = cache
        self.client = client
        self.faker = faker
        self.keeper = keeper

        self.users = lambda: None
        self.projects = lambda: None
        self.roles = self.client.roles

        self.users.get = self.client.users.get
        self.users.find = self.client.users.find
        self.users.create = self.user_create
        self.users.update = self.user_update
        self.users.delete = self.user_delete

        self.projects.get = self.client.projects.get
        self.projects.fidn = self.client.projects.find
        self.projects.create = self.project_create
        self.projects.update = self.project_update
        self.projects.delete = self.project_delete

    @cache
    def user_create(self):
        name = self.faker.name()
        password = self.faker.password()
        email = self.faker.safe_email()
        project_id = self.keeper.get_random(self.cache["keystone"]["projects"])
        project = self.keeper.get_by_id("keystone", "projects", project_id)
        user = self.client.users.create(name=name,
                                        domain="default",
                                        password=password,
                                        email=email,
                                        description=("User with name {}".
                                                     format(name)),
                                        enabled=True,
                                        default_project=project)

        self.roles.grant(self.roles.find(name="admin"), user, project=project)
        self.cache["users"][name] = {"password": password,
                                     "project_name": project.name,
                                     "project_domain_id": project.domain_id}

        return user

    @cache
    def user_update(self):
        name = self.faker.name()
        password = self.faker.password()
        email = self.faker.safe_email()
        user = None
        while user is None or user.name == "admin":
            user_id = self.keeper.get_random(self.cache["keystone"]["users"])
            user = self.keeper.get_by_id("keystone", "users", user_id)
        return self.client.users.update(user=user,
                                        name=name,
                                        domain="default",
                                        password=password,
                                        email=email,
                                        description=("User with name {}".
                                                     format(name)),
                                        enabled=True)

    @uncache
    def user_delete(self):
        user_id = self.keeper.get_random(self.cache["keystone"]["users"])
        return self.client.users.delete(
            self.keeper.get_by_id("keystone", "users", user_id))

    @cache
    def project_create(self):
        name = self.faker.word()
        return self.client.projects.create(name=name,
                                           domain="default",
                                           description=("Project {}".
                                                        format(name)),
                                           enabled=True)

    @cache
    def project_update(self):
        name = self.faker.word()
        project = None
        while project is None or project.name == "admin":
            project_id = self.keeper.get_random(
                self.cache["keystone"]["projects"])
            project = self.keeper.get_by_id("keystone", "projects", project_id)
        return self.client.projects.update(project=project,
                                           name=name,
                                           domain="default",
                                           description=("Project {}".
                                                        format(name)),
                                           enabled=True)

    @uncache
    def project_delete(self):
        project_id = self.keeper.get_random(self.cache["keystone"]["projects"])
        return self.client.projects.delete(
            self.keeper.get_by_id("keystone", "projects", project_id))


class Neutron(object):
    def __init__(self, cache):
        pass


class Cinder(object):
    def __init__(self, cache):
        pass


class Nova(object):
    def __init__(self, cache):
        pass


class Glance(object):
    def __init__(self, cache):
        pass
