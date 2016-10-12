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

import netaddr

import random

import client_factory
import faker


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

        class_name = self.__class__.__name__.lower().replace("spam", "")
        self.cache[class_name][section].setdefault(processed.id, False)

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

        class_name = self.__class__.__name__.lower().replace("spam", "")
        del self.cache[class_name][section][processed]

        return processed

    return wrapper


def come_up_subnet(neutron_subnets, length):
    subnets = []

    for neutron_subnet in neutron_subnets:
        first = netaddr.IPAddress(netaddr.IPNetwork(neutron_subnet.cidr).first)
        last = netaddr.IPAddress(netaddr.IPNetwork(neutron_subnet.cidr).last)
        subnets.extend([first, last])

    subnets.sort()
    subnets.insert(0, netaddr.IPAddress("192.0.0.0"))
    subnets.append(netaddr.IPAddress("192.255.255.255"))

    max_length = 0
    for start, end in zip(subnets[::2], subnets[1::2]):
        space_range = list(netaddr.IPRange(start, end))
        if str(start) != "192.0.0.0":
            space_range = space_range[1:]
        elif str(end) != "192.255.255.255":
            space_range = space_range[:-1]

        space_length = len(space_range)
        if space_length > max_length:
            max_length = space_length
            start_ip = str(start)
            end_ip = str(end)
        if space_length >= length:
            return netaddr.iprange_to_cidrs(space_range[0],
                                            space_range[length - 1])[0]

    return netaddr.iprange_to_cidrs(start_ip, end_ip)[0]


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

    def spam_keystone(self):
        """Create Keystone client."""

        return SpamKeystone(self.cache, self.keystone(), self.faker,
                            self.keeper)

    def spam_neutron(self):
        """Create Neutron client."""

        return SpamNeutron(self.cache, self.neutron(), self.faker, self.keeper)

    def spam_cinder(self):
        """Create Cinder client."""

        return SpamCinder(self.cache, self.cinder(), self.faker, self.keeper)

    def spam_nova(self):
        """Create Nova client."""

        return SpamNova(self.cache, self.nova(), self.faker, self.keeper)

    def spam_glance(self):
        """Create Glance client."""

        return SpamGlance(self.cache, self.glance(), self.faker, self.keeper)


class SpamKeystone(object):
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

        self.native = client

        self.cache = cache
        self.faker = faker
        self.keeper = keeper

        self.spam = lambda: None

        self.spam.users = lambda: None
        self.spam.projects = lambda: None

        self.spam.users.create = self.spam_user_create
        self.spam.users.update = self.spam_user_update
        self.spam.users.delete = self.spam_user_delete

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
        user = self.native.users.create(name=name, domain="default",
                                        password=password, email=email,
                                        description=("User with name {}".
                                                     format(name)),
                                        enabled=True,
                                        default_project=project)

        self.native.roles.grant(self.native.roles.find(name="admin"), user,
                                project=project)

        self.cache["users"][name] = {"username": user.name,
                                     "password": password,
                                     "project_name": project.name,
                                     "project_domain_id": project.domain_id,
                                     "user_domain_id": user.domain_id}

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

        self.cache["users"][name] = {"username": name,
                                     "password": password,
                                     "project_name":
                                     self.cache["users"]
                                     [user.name]["project_name"],
                                     "project_domain_id":
                                     self.cache["users"]
                                     [user.name]["project_domain_id"],
                                     "user_domain_id":
                                     self.cache["users"]
                                     [user.name]["user_domain_id"]}
        del self.cache["users"][user.name]

        return self.native.users.update(user=user, name=name, domain="default",
                                        password=password, email=email,
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

        project = self.native.projects.create(name=name, domain="default",
                                              description=("Project {}".
                                                           format(name)),
                                              enabled=True)
        # quotas update
        self.keeper.client_factory.cinder().quotas.update(
            project.id, backup_gigabytes=-1, backups=-1, gigabytes=-1,
            per_volume_gigabytes=-1, snapshots=-1, volumes=-1)
        self.keeper.client_factory.neutron().quotas.update(
            project.id, subnet=-1, network=-1, floatingip=-1, subnetpool=-1,
            port=-1, security_group_rule=-1, security_group=-1, router=-1,
            rbac_policy=-1)
        self.keeper.client_factory.nova().quotas.update(
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

        return self.native.projects.update(project=project, name=name,
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


class SpamNeutron(object):
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

        self.native = client

        self.cache = cache
        self.faker = faker
        self.keeper = keeper

        self.spam = lambda: None

        self.spam.networks = lambda: None
        self.spam.routers = lambda: None
        self.spam.ports = lambda: None
        self.spam.subnets = lambda: None

        self.spam.networks.create = self.spam_network_create
        self.spam.networks.update = self.spam_network_update
        self.spam.networks.delete = self.spam_network_delete

        self.spam.routers.create = self.spam_router_create
        self.spam.routers.update = self.spam_router_update
        self.spam.routers.delete = self.spam_router_delete

        self.spam.ports.create = self.spam_port_create
        self.spam.ports.update = self.spam_port_update
        self.spam.ports.delete = self.spam_port_delete

        self.spam.subnets.create = self.spam_subnet_create
        self.spam.subnets.update = self.spam_subnet_update
        self.spam.subnets.delete = self.spam_subnet_delete

    @cache
    def spam_network_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "networks", name) is None:
                break

        return self.native.networks.create(name=name,
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

        return self.native.networks.update(network_id, name=name,
                                           description=("Network with name {}".
                                                        format(name)))

    @uncache
    def spam_network_delete(self):
        network_id = self.keeper.get_random(self.cache["neutron"]["networks"])

        # TO-DO: Make a normal warning logging
        if network_id is None:
            return

        try:
            self.native.networks.delete(network_id)
        except Exception:
            pass

        return network_id

    @cache
    def spam_router_create(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("neutron", "routers", name) is None:
                break

        return self.native.routers.create(name=name,
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

        return self.native.routers.update(router_id, name=name,
                                          description=("Router with name {}".
                                                       format(name)))

    @uncache
    def spam_router_delete(self):
        router_id = self.keeper.get_random(self.cache["neutron"]["routers"])

        # TO-DO: Make a normal warning logging
        if router_id is None:
            return

        self.native.routers.delete(router_id)

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

        return self.native.ports.create(name=name,
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

        return self.native.ports.update(port_id, name=name,
                                        description=("Port with name {}".
                                                     format(name)))

    @uncache
    def spam_port_delete(self):
        port_id = self.keeper.get_random(self.cache["neutron"]["ports"])

        # TO-DO: Make a normal warning logging
        if port_id is None:
            return

        self.native.ports.delete(port_id)

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
        subnets = [self.keeper.get_by_id("neutron", "subnets", subnet)
                   for subnet in network.subnets]
        cidr = come_up_subnet(subnets, 2 ** random.randint(3, 4))

        return self.native.subnets.create(cidr=str(cidr), ip_version=4,
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

        return self.native.subnets.update(subnet_id, name=name,
                                          description=("Subnet with name {}".
                                                       format(name)))

    @uncache
    def spam_subnet_delete(self):
        subnet_id = self.keeper.get_random(self.cache["neutron"]["subnets"])

        # TO-DO: Make a normal warning logging
        if subnet_id is None:
            return

        self.native.subnets.update(subnet_id)

        return subnet_id


class SpamCinder(object):
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

        self.native = client

        self.cache = cache
        self.faker = faker
        self.keeper = keeper

        self.spam = lambda: None

        self.spam.volumes = lambda: None

        self.spam.volumes.create = self.volume_create
        self.spam.volumes.update = self.volume_update
        self.spam.volumes.extend = self.volume_extend
        self.spam.volumes.attach = self.volume_attach
        self.spam.volumes.detach = self.volume_detach
        self.spam.volumes.delete = self.volume_delete

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
            name = self.faker.word()
            if self.keeper.get_by_name("cinder", "volumes", name) is None:
                break

        volume_id = self.keeper.get_random(self.cache["cinder"]["volumes"])

        # TO-DO: Make a normal warning logging
        if volume_id is None:
            return

        volume = self.keeper.get_by_id("cinder", "volumes", volume_id)

        return self.native.volumes.update(volume=volume, name=name,
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


class SpamNova(object):
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

        self.native = client

        self.cache = cache
        self.faker = faker
        self.keeper = keeper

        self.spam = lambda: None

        self.spam.flavors = lambda: None
        self.spam.flavors.create = self.flavor_create
        self.spam.flavors.delete = self.flavor_delete

        self.spam.security_groups = lambda: None
        self.spam.security_groups.get = self.native.security_groups.get
        self.spam.security_groups.find = self.native.security_groups.find

        self.spam.servers = lambda: None
        self.spam.servers.create = self.server_create
        self.spam.servers.update = self.server_update

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

        server = self.native.servers.create(name=name, image=image,
                                            flavor=flavor,
                                            security_groups=security_group,
                                            nics=[{"net-id": network.id}])
        return server

    def server_update(self):
        while True:
            name = self.faker.word()
            if self.keeper.get_by_name("nova", "servers", name) is None:
                break

        server_id = self.keeper.get_random(self.cache["nova"]["servers"])

        # TO-DO: Make a normal warning logging
        if server_id is None:
            return

        server = self.keeper.get_by_id("nova", "servers", server_id)

        return self.native.servers.update(server=server, name=name)


class SpamGlance(object):
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

        self.native = client

        self.cache = cache
        self.faker = faker
        self.keeper = keeper

        self.spam = lambda: None

        self.spam.images = lambda: None
        self.spam.images.create = self.image_create
        self.spam.images.update = self.image_update

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

        if len(self.cache["glance"]["images"]) == 1:
            return

        while True:
            image_id = self.keeper.get_random(self.cache["glance"]["images"])
            image = self.keeper.get_by_id("glance", "images", image_id)
            if not image.name.startswith("cirros"):
                break

        # TO-DO: Make a normal warning logging
        if image_id is None:
            return

        image = self.native.images.update(image_id, name=name)
        return image
