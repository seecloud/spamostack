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

import argparse
import random

import faker
from openstackclient.common import clientmanager
from os_client_config import config as cloud_config


def cache(func):
    def wrapper(self, *args, **kwargs):
        processed = func(self, *args, **kwargs)
        section = ""

        if "user" in func.__name__:
            section = "users"
        elif "project" in func.__name__:
            section = "projects"
        elif "volume" in func.__name__:
            section = "volumes"
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
        del self.cache[self.__class__.__name__.lower()][section][processed]

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

        @param client: An instance of the identity client
        @type: client: `clientmanager.identity`

        @param faker: An instance of the faker object
        @type faker: `faker.Factory`

        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        self.cache = cache
        self.native = client
        self.faker = faker
        self.keeper = keeper

        self.users = lambda: None
        self.projects = lambda: None

        self.users.get = self.native.users.get
        self.users.find = self.native.users.find
        self.users.list = self.native.users.list

        self.users.create = self.user_create
        self.users.update = self.user_update
        self.users.delete = self.user_delete

        self.projects.get = self.native.projects.get
        self.projects.find = self.native.projects.find
        self.projects.list = self.native.projects.list

        self.projects.create = self.project_create
        self.projects.update = self.project_update
        self.projects.delete = self.project_delete

    @cache
    def user_create(self):
        while True:
            name = self.faker.name()
            if self.keeper.get_by_name("keystone", "users", name) is None:
                break

        password = self.faker.password()
        email = self.faker.safe_email()
        project_id = self.keeper.get_random(self.cache["keystone"]["projects"])

        # TO-DO: Make a normal warning logging
        if project_id is None:
            return

        project = self.keeper.get_by_id("keystone", "projects", project_id)
        user = self.native.users.create(name=name,
                                        domain="default",
                                        password=password,
                                        email=email,
                                        description=("User with name {}".
                                                     format(name)),
                                        enabled=True,
                                        default_project=project)

        self.native.roles.grant(self.native.roles.find(name="admin"),
                                user, project=project)
        self.cache["users"][name] = {"os_username": user.name,
                                     "os_password": password,
                                     "os_project_name": project.name,
                                     "os_project_domain_id": project.domain_id,
                                     "os_user_domain_id": user.domain_id}

        return user

    def user_update(self):
        while True:
            # TO-DO: Make a normal warning logging
            if len(self.cache["keystone"]["users"]) == 1:
                return
            name = self.faker.name()
            if self.keeper.get_by_name("keystone", "users", name) is None:
                break

        while True:
            user_id = self.keeper.get_random(self.cache["keystone"]["users"])
            user = self.keeper.get_by_id("keystone", "users", user_id)
            if user.name != "admin":
                break

        password = self.faker.password()
        email = self.faker.safe_email()

        self.cache["users"][name] = {"os_username": name,
                                     "os_password": password,
                                     "os_project_name":
                                     self.cache["users"]
                                     [user.name]["os_project_name"],
                                     "os_project_domain_id":
                                     self.cache["users"]
                                     [user.name]["os_project_domain_id"],
                                     "os_user_domain_id":
                                     self.cache["users"]
                                     [user.name]["os_user_domain_id"]}
        del self.cache["users"][user.name]

        return self.native.users.update(user=user,
                                        name=name,
                                        domain="default",
                                        password=password,
                                        email=email,
                                        description=("User with name {}".
                                                     format(name)),
                                        enabled=True)

    @uncache
    def user_delete(self):
        while True:
            # TO-DO: Make a normal warning logging
            if len(self.cache["keystone"]["users"]) == 1:
                return
            user_id = self.keeper.get_random(self.cache["keystone"]["users"])
            user = self.keeper.get_by_id("keystone", "users", user_id)
            if user.name != "admin":
                break

        self.native.users.delete(user)
        return user_id

    @cache
    def project_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("keystone", "projects", name) is None:
                break

        project = self.native.projects.create(name=name,
                                              domain="default",
                                              description=("Project {}".
                                                           format(name)),
                                              enabled=True)
        # quotas update
        self.keeper.client_factory.cinder().native.quotas.update(
            project.id, backup_gigabytes=-1, backups=-1, gigabytes=-1,
            per_volume_gigabytes=-1, snapshots=-1, volumes=-1)
        self.keeper.client_factory.neutron().native.update_quota(
            project.id, subnet=-1, network=-1, floatingip=-1, subnetpool=-1,
            port=-1, security_group_rule=-1, security_group=-1, router=-1,
            rbac_policy=-1)
        self.keeper.client_factory.nova().native.quotas.update(
            project.id, cores=-1, fixed_ips=-1, floating_ips=-1,
            injected_file_content_bytes=-1, injected_file_path_bytes=-1,
            injected_files=-1, instances=-1, key_pairs=-1, metadata_items=-1,
            ram=-1, security_group_rules=-1, security_groups=-1,
            server_group_members=-1, server_groups=-1)

        return project

    def project_update(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("keystone", "projects", name) is None:
                break

        while True:
            # TO-DO: Make a normal warning logging
            if len(self.cache["keystone"]["projects"]) == 1:
                return
            project_id = self.keeper.get_random(
                self.cache["keystone"]["projects"])
            project = self.keeper.get_by_id("keystone", "projects", project_id)
            if project.name != "admin":
                break

        return self.native.projects.update(project=project,
                                           name=name,
                                           domain="default",
                                           description=("Project {}".
                                                        format(name)),
                                           enabled=True)

    @uncache
    def project_delete(self):
        while True:
            # TO-DO: Make a normal warning logging
            if len(self.cache["keystone"]["projects"]) == 1:
                return
            project_id = self.keeper.get_random(
                self.cache["keystone"]["projects"])
            project = self.keeper.get_by_id("keystone", "projects", project_id)
            if project.name != "admin":
                break

        self.native.projects.delete(project)
        return project_id


class Neutron(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `Neutron` class instance.

        @param cache: Cache
        @type cache: `cache.Cache`

        @param client: An instance of the identity client
        @type: client: `clientmanager.identity`

        @param faker: An instance of the faker object
        @type faker: `faker.Factory`

        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        self.cache = cache
        self.native = client
        self.faker = faker
        self.keeper = keeper


class Cinder(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `Cinder` class instance.

        @param cache: Cache
        @type cache: `cache.Cache`

        @param client: An instance of the identity client
        @type: client: `clientmanager.identity`

        @param faker: An instance of the faker object
        @type faker: `faker.Factory`

        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        self.cache = cache
        self.native = client
        self.faker = faker
        self.keeper = keeper

        self.volumes = lambda: None

        self.volumes.get = self.native.volumes.get
        self.volumes.find = self.native.volumes.find
        self.volumes.list = self.native.volumes.list

        self.volumes.create = self.volume_create
        self.volumes.update = self.volume_update
        self.volumes.extend = self.volume_extend
        self.volumes.attach = self.volume_attach
        self.volumes.detach = self.volume_detach
        self.volumes.delete = self.volume_delete

    @cache
    def volume_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("cinder", "volumes", name) is None:
                break
        volume_sizes = [1, 2, 5, 10, 20, 40, 50]
        volume = self.native.volumes.create(name=name,
                                            size=random.choice(volume_sizes),
                                            description=("Volume with name {}".
                                                         format(name)))
        self.native.volumes.reset_state(volume, "available", "detached")

        return volume

    def volume_update(self):
        while True:
            name = self.faker.name()
            if self.keeper.get_by_name("cinder", "volumes", name) is None:
                break

        volume_id = self.keeper.get_random(self.cache["cinder"]["volumes"])

        # TO-DO: Make a normal warning logging
        if volume_id is None:
            return

        volume = self.keeper.get_by_id("cinder", "volumes", volume_id)

        return self.native.volumes.update(volume=volume,
                                          name=name,
                                          description=("Volume with name {}".
                                                       format(name)))

    def volume_extend(self):
        volume_id = self.keeper.get_random(self.cache["cinder"]["volumes"])

        # TO-DO: Make a normal warning logging
        if volume_id is None:
            return

        volume = self.keeper.get_by_id("cinder", "volumes", volume_id)
        add_size = random.randint(1, 10)

        return self.native.volumes.extend(volume=volume,
                                          new_size=volume.size + add_size)

    def volume_attach(self):
        volume_id = self.keeper.get_unused(self.cache["cinder"]["volumes"])

        # TO-DO: Make a normal warning logging
        if volume_id is None:
            return

        self.cache["cinder"]["volumes"][volume_id] = True
        volume = self.keeper.get_by_id("cinder", "volumes", volume_id)
        instance_id = self.keeper.get_random(self.cache["nova"]["servers"])

        # TO-DO: Make a normal warning logging
        if instance_id is None:
            return

        return self.native.volumes.attach(volume, instance_id, volume.name)

    def volume_detach(self):
        volume_id = self.keeper.get_used(self.cache["cinder"]["volumes"])

        # TO-DO: Make a normal warning logging
        if volume_id is None:
            return

        self.cache["cinder"]["volumes"][volume_id] = False
        volume = self.keeper.get_by_id("cinder", "volumes", volume_id)

        return self.native.volumes.detach(volume)

    @uncache
    def volume_delete(self):
        volume_id = self.keeper.get_random(self.cache["cinder"]["volumes"])

        # TO-DO: Make a normal warning logging
        if volume_id is None:
            return

        volume = self.keeper.get_by_id("cinder", "volumes", volume_id)
        self.native.volumes.delete(volume)

        return volume_id


class Glance(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `Glance` class instance.

        @param cache: Cache
        @type cache: `cache.Cache`

        @param client: An instance of the identity client
        @type: client: `clientmanager.identity`

        @param faker: An instance of the faker object
        @type faker: `faker.Factory`

        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        self.cache = cache
        self.native = client
        self.faker = faker
        self.keeper = keeper


class Nova(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `Nova` class instance.

        @param cache: Cache
        @type cache: `cache.Cache`

        @param client: An instance of the identity client
        @type: client: `clientmanager.identity`

        @param faker: An instance of the faker object
        @type faker: `faker.Factory`

        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        self.cache = cache
        self.native = client
        self.faker = faker
        self.keeper = keeper
