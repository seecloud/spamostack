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
import netaddr

import faker
from openstackclient.common import clientmanager
from os_client_config import config as cloud_config
import client_factory 


def cache(func):
    def wrapper(self, *args, **kwargs):
        processed = func(self, *args, **kwargs)
        if processed is None:
            return
        section = ""

        if "user" in func.__name__:
            section = "users"
        elif "project" in func.__name__:
            section = "projects"
        elif "volume" in func.__name__:
            section = "volumes"
        elif "network" in func.__name__:
            section = "networks"
        elif "router" in func.__name__:
            section = "routers"
        elif "port" in func.__name__:
            section = "ports"
        elif "flavor" in func.__name__:
            section = "flavors"
        elif "server" in func.__name__:
            section = "servers"
        elif "image" in func.__name__:
            section = "images"
        (self.cache[self.__class__.__name__.lower()][section].
         setdefault(processed.id, False))

        return processed

    return wrapper


def uncache(func):
    def wrapper(self, *args, **kwargs):
        processed = func(self, *args, **kwargs)
        if processed is None:
            return
        section = ""

        if "user" in func.__name__:
            section = "users"
        elif "project" in func.__name__:
            section = "projects"
        elif "volume" in func.__name__:
            section = "volumes"
        elif "network" in func.__name__:
            section = "networks"
        elif "router" in func.__name__:
            section = "routers"
        elif "port" in func.__name__:
            section = "ports"
        elif "flavor" in func.__name__:
            section = "flavors"
        elif "server" in func.__name__:
            section = "servers"
        elif "image" in func.__name__:
            section = "images"
        del self.cache[self.__class__.__name__.lower()][section][processed]

        return processed

    return wrapper


def come_up_subnet(neutron_subnets, length):
    subnets = []

    for neutron_subnet in neutron_subnets:
        first = netaddr.IPAddress(netaddr.IPNetwork(neutron_subnet.cidr).first)
        last = netaddr.IPAddress(netaddr.IPNetwork(neutron_subnet.cidr).last)
        subnets.append(first, last)

    subnets.sort()
    if len(subnets) == 0 or str(subnets[0]) != "192.0.0.0":
        subnets.insert(0, netaddr.IPAddress("192.0.0.0"))
    if len(subnets) == 0 or str(subnets[-1]) != "192.255.255.255":
        subnets.insert(0, netaddr.IPAddress("192.255.255.255"))

    max_length = 0
    for start, end in zip(subnets[::2], subnets[1::2]):
        space_range = netaddr.IPRange(start, end)
        space_length = len(space_range)
        if space_length > max_length:
            max_length = space_length
            start_ip = start
            end_ip = end
        if space_length >= length:
            return netaddr.IPNetwork(space_range[0], space_range[length - 1])

    return netaddr.IPNetwork(start_ip, end_ip)


class SpamFactory(client_factory.ClientFactory, object):
    def __init__(self, cache, user, keeper=None):
        """Create instance of `SpamFactory` class

        @param cahce: Reference to the cache
        @type cache: spamostack.cache.Cache

        @param user: User for client factory instance
        @type user: `dict` or `User`

        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        super(SpamFactory, self).__init__(user)

        self.cache = cache
        self.keeper = keeper
        self.faker = faker.Factory.create('en_US')

    def keystone(self):
        """Create Keystone client."""

        return SpamKeystone(self.cache, self.client_manager.identity, self.faker,
                        self.keeper)

    def neutron(self):
        """Create Neutron client."""

        return SpamNeutron(self.cache, self.client_manager.network, self.faker,
                       self.keeper)

    def cinder(self):
        """Create Cinder client."""

        return SpamCinder(self.cache, self.client_manager.volume, self.faker,
                      self.keeper)

    def nova(self):
        """Create Nova client."""

        return SpamNova(self.cache, self.client_manager.compute, self.faker,
                    self.keeper)

    def glance(self):
        """Create Glance client."""

        return SpamGlance(self.cache, self.client_manager.image, self.faker,
                      self.keeper)


class SpamKeystone(client_factory.Keystone, object):
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

        super(SpamKeystone, self).__init__(client)

        self.cache = cache
        self.faker = faker
        self.keeper = keeper

        self.spam.users = lambda: None
        self.spam.projects = lambda: None

        self.users = self.native.users

        self.spam.users.create = self.spam_user_create
        self.spam.users.update = self.spam_user_update
        self.spam.users.delete = self.spam_user_delete

        self.projects = self.native.projects

        self.spam.projects.create = self.spam_project_create
        self.spam.projects.update = self.spam_project_update
        self.spam.projects.delete = self.spam_project_delete

    @cache
    def spam_user_create(self):
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

    def spam_user_update(self):
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
    def spam_user_delete(self):
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
    def spam_project_create(self):
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

    def spam_project_update(self):
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
    def spam_project_delete(self):
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

        self.spam.networks = lambda: None
        self.spam.routers = lambda: None
        self.spam.ports = lambda: None
        self.spam.subnets = lambda: None

        self.networks.get = self.native.get_network
        self.networks.find = self.native.find_network
        self.networks.list = self.native.networks

        self.spam.networks.create = self.spam_network_create
        self.spam.networks.update = self.spam_network_update
        self.spam.networks.delete = self.spam_network_delete

        self.routers.get = self.native.get_router
        self.routers.find = self.native.find_router
        self.routers.list = self.native.routers

        self.spam.routers.create = self.spam_router_create
        self.spam.routers.update = self.spam_router_update
        self.spam.routers.delete = self.spam_router_delete

        self.ports.get = self.native.get_port
        self.ports.find = self.native.find_port
        self.ports.list = self.native.ports

        self.spam.ports.create = self.spam_port_create
        self.spam.ports.update = self.spam_port_update
        self.spam.ports.delete = self.spam_port_delete

        self.subnets.get = self.native.get_subnet
        self.subnets.find = self.native.find_subnet
        self.subnets.list = self.native.subnets

        self.spam.subnets.create = self.spam_subnet_create
        self.spam.subnets.update = self.spam_subnet_update
        self.spam.subnets.delete = self.spam_subnet_delete

    @cache
    def spam_network_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "networks", name) is None:
                break

        return self.native.create_network(name=name,
                                          description=("Network with name {}".
                                                       format(name)),
                                          shared=True)

    def spam_network_update(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "networks", name) is None:
                break

        network_id = self.keeper.get_random(self.cache["neutron"]["networks"])

        # TO-DO: Make a normal warning logging
        if network_id is None:
            return

        return self.native.update_network(network_id, name=name,
                                          description=("Network with name {}".
                                                       format(name)))

    @uncache
    def spam_network_delete(self):
        network_id = self.keeper.get_random(self.cache["neutron"]["networks"])

        # TO-DO: Make a normal warning logging
        if network_id is None:
            return

        self.native.delete_network(network_id)

        return network_id

    @cache
    def spam_router_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "routers", name) is None:
                break

        return self.native.create_router(name=name,
                                         description=("Router with name {}".
                                                      format(name)))

    def spam_router_update(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "routers", name) is None:
                break

        router_id = self.keeper.get_random(self.cache["neutron"]["routers"])

        # TO-DO: Make a normal warning logging
        if router_id is None:
            return

        return self.native.update_router(router_id, name=name,
                                         description=("Router with name {}".
                                                      format(name)))

    @uncache
    def spam_router_delete(self):
        router_id = self.keeper.get_random(self.cache["neutron"]["routers"])

        # TO-DO: Make a normal warning logging
        if router_id is None:
            return

        self.native.delete_router(router_id)

        return router_id

    @cache
    def spam_port_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "ports", name) is None:
                break

        network_id = self.keeper.get_random(self.cache["neutron"]["networks"])

        # TO-DO: Make a normal warning logging
        if network_id is None:
            return

        return self.native.create_port(name=name,
                                       description=("Port with name {}".
                                                    format(name)),
                                       network_id=network_id)

    def spam_port_update(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "ports", name) is None:
                break

        port_id = self.keeper.get_random(self.cache["neutron"]["ports"])

        # TO-DO: Make a normal warning logging
        if port_id is None:
            return

        return self.native.update_port(port_id, name=name,
                                       description=("Port with name {}".
                                                    format(name)))

    @uncache
    def spam_port_delete(self):
        port_id = self.keeper.get_random(self.cache["neutron"]["ports"])

        # TO-DO: Make a normal warning logging
        if port_id is None:
            return

        self.native.delete_port(port_id)

        return port_id

    @cache
    def spam_subnet_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "subnets", name) is None:
                break

        network_id = self.keeper.get_random(self.cache["neutron"]["networks"])

        # TO-DO: Make a normal warning logging
        if network_id is None:
            return

        network = self.keeper.get_by_id("neutron", "networks", network_id)
        cidr = come_up_subnet([subnet for subnet in network.subnets],
                              random.randint(1, 16))

        return self.native.create_subnet(cidr=str(cidr),
                                         ip_version=4,
                                         name=name,
                                         description=("Subnet with name {}".
                                                      format(name)),
                                         network_id=network_id)

    def spam_subnet_update(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "subnets", name) is None:
                break

        subnet_id = self.keeper.get_random(self.cache["neutron"]["subnets"])

        # TO-DO: Make a normal warning logging
        if subnet_id is None:
            return

        return self.native.update_subnet(subnet_id, name=name,
                                         description=("Subnet with name {}".
                                                      format(name)))

    @uncache
    def spam_subnet_delete(self):
        subnet_id = self.keeper.get_random(self.cache["neutron"]["subnets"])

        # TO-DO: Make a normal warning logging
        if subnet_id is None:
            return

        self.native.delete_subnet(subnet_id)

        return subnet_id


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

        self.flavors = lambda: None
        self.flavors.get = self.native.flavors.get
        self.flavors.find = self.native.flavors.find
        self.flavors.create = self.flavor_create
        self.flavors.delete = self.flavor_delete

        self.security_groups = lambda: None
        self.security_groups.get = self.native.security_groups.get
        self.security_groups.find = self.native.security_groups.find

        self.servers = lambda: None
        self.servers.get = self.native.servers.get
        self.servers.find = self.native.servers.find
        self.servers.create = self.server_create
        self.servers.update = self.server_update

    @cache
    def flavor_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("nova", "flavors", name) is None:
                break
        return self.native.flavors.create(name, 1, 1, 1)

    @uncache
    def flavor_delete(self):
        pass

    @cache
    def server_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("nova", "servers", name) is None:
                break

        image_id = self.keeper.get_random(self.cache["glance"]["images"])
        image = self.keeper.get_by_id("glance", "images", image_id)
        flavor_id = self.keeper.get_random(self.cache["nova"]["flavors"])
        flavor = self.keeper.get_by_id("nova", "flavors", flavor_id)
        if "security_groups" in self.cache["nova"]:
            # FIXME (mivanov) Fix security groups assigning ASAP
            security_group = None
            # security_group_id = self.keeper.get_random(
            #    self.cache["nova"]["security_groups"])
            # security_group = self.keeper.get_by_id(
            #    "nova", "security_groups", security_group_id)
        else:
            security_group = None

        network = self.keeper.get("neutron", "networks", "subnets",
                                  lambda x: len(x) > 0)

        # TO-DO: Make a normal warning logging
        if network is None:
            return

        return self.native.servers.create(name=name, image=image,
                                          flavor=flavor,
                                          security_groups=security_group,
                                          nics=[{"net-id": network.id}])

    def server_update(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("nova", "servers", name) is None:
                break

        server_id = self.keeper.get_random(
            self.cache["nova"]["servers"])
        return self.native.servers.update(server=server_id, name=name)


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

        self.images = lambda: None
        self.images.get = self.native.images.get
        self.images.list = self.native.images.list
        self.images.find = self.find
        self.images.create = self.image_create
        self.images.update = self.image_update

    def find(self, **kwargs):
        return list(self.native.images.list(filters=kwargs))[0]

    @cache
    def image_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("glance", "images", name) is None:
                break
        image = self.native.images.create(name=name, data=name,
                                          disk_format='raw',
                                          container_format='bare',
                                          visibility='public')
        self.native.images.upload(image.id, '')
        return image

    def image_update(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("glance", "images", name) is None:
                break
        image_id = self.keeper.get_random(self.cache["glance"]["images"])
        image = self.native.images.update(image_id, name=name)
        return image
