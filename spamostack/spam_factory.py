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

import logging
import random

import client_factory
from Crypto.PublicKey import RSA
import faker
import netaddr

log = logging.getLogger(__name__)


def cache(func):
    def wrapper(self, *args, **kwargs):
        processed = func(self, *args, **kwargs)
        if processed is None:
            return
        section = ""

        if "container" in func.__name__:
            section = "containers"
        elif "flavor" in func.__name__:
            section = "flavors"
        elif "image" in func.__name__:
            section = "images"
        elif "keypair" in func.__name__:
            section = "keypairs"
        elif "network" in func.__name__:
            section = "networks"
        elif "object" in func.__name__:
            section = "objects"
        elif "port" in func.__name__:
            section = "ports"
        elif "project" in func.__name__:
            section = "projects"
        elif "router" in func.__name__:
            section = "routers"
        elif "security_groups" in func.__name__:
            section = "security_groups"
        elif "server" in func.__name__:
            section = "servers"
        elif "subnet" in func.__name__:
            section = "subnets"
        elif "user" in func.__name__:
            section = "users"
        elif "volume" in func.__name__:
            section = "volumes"

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

        if "container" in func.__name__:
            section = "containers"
        elif "flavor" in func.__name__:
            section = "flavors"
        elif "image" in func.__name__:
            section = "images"
        elif "keypair" in func.__name__:
            section = "keypairs"
        elif "network" in func.__name__:
            section = "networks"
        elif "object" in func.__name__:
            section = "objects"
        elif "port" in func.__name__:
            section = "ports"
        elif "project" in func.__name__:
            section = "projects"
        elif "router" in func.__name__:
            section = "routers"
        elif "security_groups" in func.__name__:
            section = "security_groups"
        elif "server" in func.__name__:
            section = "servers"
        elif "subnet" in func.__name__:
            section = "subnets"
        elif "user" in func.__name__:
            section = "users"
        elif "volume" in func.__name__:
            section = "volumes"

        class_name = self.__class__.__name__.lower().replace("spam", "")
        del self.cache[class_name][section][processed]

        return processed

    return wrapper


def come_up_subnet(neutron_subnets, size):
    """Come ups subnets with specific size

    @param neutron_subnets: List of neutron subnets
    @type neutron_subnets: `list(client_factory.Accessible)`

    @param size: Size of future subnet
    @type size: `int`
    """

    log.info("Start generating of subnets")
    subnets = []

    for neutron_subnet in neutron_subnets:
        first = netaddr.IPAddress(netaddr.IPNetwork(neutron_subnet.cidr).first)
        last = netaddr.IPAddress(netaddr.IPNetwork(neutron_subnet.cidr).last)
        subnets.extend([first, last])

    subnets.sort()
    subnets.insert(0, netaddr.IPAddress("192.0.0.0"))
    subnets.append(netaddr.IPAddress("192.255.255.255"))

    max_size = 0
    for start, end in zip(subnets[::2], subnets[1::2]):
        space_range = list(netaddr.IPRange(start, end))
        if str(start) != "192.0.0.0":
            space_range = space_range[1:]
        elif str(end) != "192.255.255.255":
            space_range = space_range[:-1]

        space_size = len(space_range)
        if space_size > max_size:
            max_size = space_size
            start_ip = str(start)
            end_ip = str(end)
        if space_size >= size:
            return netaddr.iprange_to_cidrs(space_range[0],
                                            space_range[size - 1])[0]

    return netaddr.iprange_to_cidrs(start_ip, end_ip)[0]


class SpamFactory(client_factory.ClientFactory, object):
    def __init__(self, cache, user, keeper=None):
        """Create instance of `SpamFactory` class

        @param cahce: Reference to the cache
        @type cache: spamostack.cache.Cache

        @param user: User for client factory instance
        @type user: `dict`

        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        super(SpamFactory, self).__init__(user)

        self.cache = cache
        self.keeper = keeper
        self.faker = faker.Factory.create('en_US')

    def spam_cinder(self):
        """Create spam cinder client."""

        return SpamCinder(self.cache, self.cinder(), self.faker, self.keeper)

    def spam_glance(self):
        """Create spam glance client."""

        return SpamGlance(self.cache, self.glance(), self.faker, self.keeper)

    def spam_keystone(self):
        """Create spam keystone client."""

        return SpamKeystone(self.cache, self.keystone(), self.faker,
                            self.keeper)

    def spam_neutron(self):
        """Create spam neutron client."""

        return SpamNeutron(self.cache, self.neutron(), self.faker, self.keeper)

    def spam_nova(self):
        """Create spam nova client."""

        return SpamNova(self.cache, self.nova(), self.faker, self.keeper)

    def spam_swift(self):
        """Create spam swift client."""

        return SpamSwift(self.cache, self.swift(), self.faker, self.keeper)


class SpamCinder(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `SpamCinder` class instance.

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

        self.spam.volumes.attach = self.volume_attach
        self.spam.volumes.create = self.volume_create
        self.spam.volumes.detach = self.volume_detach
        self.spam.volumes.delete = self.volume_delete
        self.spam.volumes.extend = self.volume_extend
        self.spam.volumes.update = self.volume_update

    def volume_attach(self):
        volumes = self.keeper.get("cinder", "volumes", None,
                                  (lambda x, y: x == [] and
                                   y in self.cache["cinder"]["volumes"]),
                                  "attachments", "id")

        if len(volumes) > 0:
            volume = random.choice(volumes)
        else:
            log.warning("There is no volumes for attaching, skipping...")
            return

        instance = self.keeper.get("nova", "servers")

        if instance is None:
            log.warning("There is no instances for volume "
                        "attaching, skipping...")
            return

        try:
            log.info("Attaching volume {volume_id} to instance {instance_id}".
                     format(volume_id=volume.id, instance_id=instance.id))
            attached = self.native.volumes.attach(
                volume, instance.id, volume.name)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return attached

    @cache
    def volume_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("cinder", "volumes", "name",
                                   lambda x: x == name):
                break

        volume_sizes = [1, 2, 5, 10, 20, 40, 50, 100, 200, 500]

        try:
            log.info("Creating new volume with name {}".format(name))
            created = self.native.volumes.create(
                name=name, size=random.choice(volume_sizes),
                description="Volume with name {}".format(name))
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        self.native.volumes.reset_state(created, "available", "detached")

        return created

    def volume_detach(self):
        volumes = self.keeper.get("cinder", "volumes", None,
                                  (lambda x, y: x != [] and
                                   y in self.cache["cinder"]["volumes"]),
                                  "attachments", "id")

        if len(volumes) > 0:
            volume = random.choice(volumes)
        else:
            log.warning("There is no volumes for detaching, skipping...")
            return

        try:
            log.info("Detaching volume {}".format(volume.id))
            detached = self.native.volumes.detach(volume)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return detached

    @uncache
    def volume_delete(self):
        volumes = self.keeper.get(
            "cinder", "volumes", "id",
            lambda x: x in self.cache["cinder"]["volumes"])

        if len(volumes) > 0:
            volume = random.choice(volumes)
        else:
            log.warning("There is no volumes for removing, skipping...")
            return

        if len(volume.attachments) > 0:
            self.native.volumes.detach(volume)

        try:
            log.info("Remove volume {}".format(volume.id))
            self.native.volumes.delete(volume)
        except Exception:
            return

        return volume.id

    def volume_extend(self):
        volumes = self.keeper.get(
            "cinder", "volumes", "id",
            lambda x: x in self.cache["cinder"]["volumes"])

        if len(volumes) > 0:
            volume = random.choice(volumes)
        else:
            log.warning("There is no volume for extending, skipping...")
            return

        add_size = random.randint(1, 100)

        try:
            log.info("Extends volume with id {}".format(volume.id))
            extended = self.native.volumes.extend(
                volume=volume, new_size=volume.size + add_size)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return extended

    def volume_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("cinder", "volumes", "name",
                                   lambda x: x == name):
                break

        volumes = self.keeper.get(
            "cinder", "volumes", "id",
            lambda x: x in self.cache["cinder"]["volumes"])

        if len(volumes) > 0:
            volume = random.choice(volumes)
        else:
            log.warning("There is no volume for updating, skipping...")
            return

        try:
            log.info("Updating volume with id {}".format(volume.id))
            updated = self.native.volumes.update(
                volume=volume, name=name,
                description="Volume with name {}".format(name))
        except Exception as exc:
            log.critical("Exception: ".format(exc))
            return

        return updated


class SpamGlance(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `SpamGlance` class instance.

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
        self.spam.images.delete = self.image_delete
        self.spam.images.update = self.image_update

    @cache
    def image_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("glance", "images", "name",
                                   lambda x: x == name):
                break

        try:
            log.info("Creating image with name {}".format(name))
            created = self.native.images.create(
                name=name, data=name, disk_format='raw',
                container_format='bare', visibility='public')
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        self.native.images.upload(created.id, '')

        return created

    @uncache
    def image_delete(self):
        images = self.keeper.get("glance", "images", None,
                                 (lambda x, y: not x.startswith("cirros") and
                                  y in self.cache["glance"]["images"]))

        if len(images) > 0:
            image = random.choice(images)
        else:
            log.warning("There is no images for removing, skipping...")
            return

        try:
            log.info("Removing image {}".format(image.id))
            self.native.images.delete(image.id)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return image.id

    def image_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("glance", "images", "name",
                                   lambda x: x == name):
                break

        images = self.keeper.get("glance", "images", None,
                                 (lambda x, y: not x.startswith("cirros") and
                                  y in self.cache["glance"]["images"]),
                                 "name", "id")

        if len(images) > 0:
            image = random.choice(images)
        else:
            log.warning("There is no images for updating, skipping")
            return

        # TO-DO: Make a normal warning logging
        try:
            log.info("Updating image {}".format(image.id))
            updated = self.native.images.update(image.id, name=name)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return updated


class SpamKeystone(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `SpamKeystone` class instance.

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

        self.spam.projects = lambda: None
        self.spam.users = lambda: None

        self.spam.projects.create = self.spam_project_create
        self.spam.projects.delete = self.spam_project_delete
        self.spam.projects.update = self.spam_project_update

        self.spam.users.create = self.spam_user_create
        self.spam.users.delete = self.spam_user_delete
        self.spam.users.update = self.spam_user_update

    @cache
    def spam_project_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("keystone", "projects", "name",
                                   lambda x: x == name):
                break

        try:
            log.info("Creating project with name {}".format(name))
            created = self.native.projects.create(
                name=name, domain="default",
                description="Project {}".format(name), enabled=True)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        # quotas update
        try:
            log.info("Update cinder quotas for project "
                     "{}".format(created.name))
            self.keeper.client_factory.cinder().quotas.update(
                created.id, backup_gigabytes=-1, backups=-1, gigabytes=-1,
                per_volume_gigabytes=-1, snapshots=-1, volumes=-1)
            log.info(
                "Update neutron quotas for project {}".format(created.name))
            self.keeper.client_factory.neutron().quotas.update(
                created.id, subnet=-1, network=-1, floatingip=-1,
                subnetpool=-1, port=-1, security_group_rule=-1,
                security_group=-1, router=-1, rbac_policy=-1)
            log.info("Update nova quotas for project {}".format(created.name))
            self.keeper.client_factory.nova().quotas.update(
                created.id, cores=-1, fixed_ips=-1, floating_ips=-1,
                injected_file_content_bytes=-1, injected_file_path_bytes=-1,
                injected_files=-1, instances=-1, key_pairs=-1,
                metadata_items=-1, ram=-1, security_group_rules=-1,
                security_groups=-1, server_group_members=-1, server_groups=-1)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def spam_project_delete(self):
        projects = self.keeper.get("keystone", "projects", None,
                                   (lambda x, y: x != "admin" and
                                    y in self.cache["keystone"]["projects"]),
                                   "name", "id")

        # TO-DO: Make a normal warning logging
        if len(projects) > 0:
            project = random.choice(projects)
        else:
            log.warning("There is no projects for removing, skipping...")
            return

        # TO-DO: Make a normal warning logging
        try:
            log.info("Removing project {}".format(project.name))
            self.native.projects.delete(project)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return project.id

    def spam_project_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("keystone", "projects", "name",
                                   lambda x: x == name):
                break

        projects = self.keeper.get("keystone", "projects", None,
                                   (lambda x, y: x != "admin" and
                                    y in self.cache["keystone"]["projects"]),
                                   "name", "id")

        # TO-DO: Make a normal warning logging
        if len(projects) > 0:
            project = random.choice(projects)
        else:
            log.warning("There is no project for updating, skipping...")
            return

        try:
            log.info("Trying to update project {}".format(project.name))
            updated = self.native.projects.update(
                project=project, name=name, domain="default",
                description="Project {}".format(name), enabled=True)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return updated

    @cache
    def spam_user_create(self):
        while True:
            name = self.faker.name()
            if not self.keeper.get("keystone", "users", "name",
                                   lambda x: x == name):
                break

        password = self.faker.password()
        email = self.faker.safe_email()

        projects = self.keeper.get(
            "keystone", "projects", "id",
            lambda x: x in self.cache["keystone"]["projects"])

        if len(projects) > 0:
            project = random.choice(projects)
        else:
            log.warning("There is no projects, skipping user creating...")
            return

        # TO-DO: Make a normal warning logging
        try:
            log.info("Creating user with name {user_name}"
                     " in project {project}".format(user_name=name,
                                                    project=project.name))
            created = self.native.users.create(
                name=name, domain="default", password=password, email=email,
                description="User with name {}".format(name), enabled=True,
                default_project=project)
            log.info("User with id {} was created".format(created.id))
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        try:
            log.info("Granting role to user {}".format(created.id))
            self.native.roles.grant(
                self.native.roles.find(name="admin"), created, project=project)
        except Exception as exc:
            log.critical("Exception: ".format(exc))
            return

        self.cache["users"][name] = {"username": created.name,
                                     "password": password,
                                     "project_name": project.name,
                                     "project_domain_id": project.domain_id,
                                     "user_domain_id": created.domain_id}

        return created

    @uncache
    def spam_user_delete(self):
        users = self.keeper.get("keystone", "users", None,
                                (lambda x, y: x != "admin" and
                                 y in self.cache["keystone"]["users"]),
                                "name", "id")

        if len(users) > 0:
            user = random.choice(users)
        else:
            log.warning("There is no users, skipping user removing...")
            return

        try:
            log.info("Trying to delete user {}".format(user.name))
            self.native.users.delete(user)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return user.id

    def spam_user_update(self):
        while True:
            name = self.faker.name()
            if not self.keeper.get("keystone", "users", "name",
                                   lambda x: x == name):
                break

        users = self.keeper.get("keystone", "users", None,
                                (lambda x, y: x != "admin" and
                                 y in self.cache["keystone"]["users"]),
                                "name", "id")

        # TO-DO: Make a normal warning logging
        if len(users) > 0:
            user = random.choice(users)
        else:
            return

        log.info("Trying to update user {}".format(user.id))
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

        try:
            updated = self.native.users.update(
                user=user, name=name, domain="default",
                password=password, email=email,
                description="User with name {}".format(name), enabled=True)
        except Exception as exc:
            log.critical("Exception: ".format(exc))
            return

        return updated


class SpamNeutron(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `SpamNeutron` class instance.

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
        self.spam.ports = lambda: None
        self.spam.routers = lambda: None
        self.spam.security_groups = lambda: None
        self.spam.subnets = lambda: None

        self.spam.networks.create = self.spam_network_create
        self.spam.networks.delete = self.spam_network_delete
        self.spam.networks.update = self.spam_network_update

        self.spam.ports.create = self.spam_port_create
        self.spam.ports.delete = self.spam_port_delete
        self.spam.ports.update = self.spam_port_update

        self.spam.routers.create = self.spam_router_create
        self.spam.routers.delete = self.spam_router_delete
        self.spam.routers.update = self.spam_router_update

        self.spam.security_groups.create = self.spam_security_group_create
        self.spam.security_groups.delete = self.spam_security_group_delete
        self.spam.security_groups.update = self.spam_security_group_update

        self.spam.subnets.create = self.spam_subnet_create
        self.spam.subnets.delete = self.spam_subnet_delete
        self.spam.subnets.update = self.spam_subnet_update

    @cache
    def spam_network_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "networks", "name",
                                   lambda x: x == name):
                break

        try:
            log.info("Creating network {}".format(name))
            created = self.native.networks.create(
                name=name, description="Network with name {}".format(name),
                shared=True)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def spam_network_delete(self):
        networks = self.keeper.get(
            "neutron", "networks", "id",
            lambda x: x in self.cache["neutron"]["networks"])

        if len(networks) > 0:
            network = random.choice(networks)
        else:
            log.warning("There is no network for removing, skipping...")
            return

        try:
            log.info("Deleting network with id {}".format(network.id))
            self.native.networks.delete(network.id)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return network.id

    def spam_network_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "networks", "name",
                                   lambda x: x == name):
                break

        networks = self.keeper.get(
            "neutron", "networks", "id",
            lambda x: x in self.cache["neutron"]["networks"])

        if len(networks) > 0:
            network = random.choice(networks)
        else:
            log.warning("There is no networks for updating, skipping")
            return

        try:
            log.info("Updating network {}".format(network.id))
            updated = self.native.networks.update(
                network.id, name=name,
                description="Network with name {}".format(name))
        except Exception:
            return

        return updated

    @cache
    def spam_port_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "ports", "name",
                                   lambda x: x == name):
                break

        networks = self.keeper.get(
            "neutron", "networks", "id",
            lambda x: x in self.cache["neutron"]["networks"])

        if len(networks) > 0:
            network = random.choice(networks)
        else:
            log.warning("There is no networks for port creating, skipping...")
            return

        try:
            log.info("Creating port with name {}".format(name))
            created = self.native.ports.create(
                name=name, description="Port with name {}".format(name),
                network_id=network.id)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def spam_port_delete(self):
        ports = self.keeper.get(
            "neutron", "ports", "id",
            lambda x: x in self.cache["neutron"]["ports"])

        if len(ports) > 0:
            port = random.choice(ports)
        else:
            log.warning("There is no ports for removing, skipping...")
            return

        try:
            log.info("Removing port with id {}".format(port.id))
            self.native.ports.delete(port.id)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return port.id

    def spam_port_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "ports", "name",
                                   lambda x: x == name):
                break

        ports = self.keeper.get(
            "neutron", "ports", "id",
            lambda x: x in self.cache["neutron"]["ports"])

        if len(ports) > 0:
            port = random.choice(ports)
        else:
            log.warning("There is no ports for updating, skipping...")
            return

        try:
            log.info("Update port with id {}".format(port.id))
            updated = self.native.ports.update(
                port.id, name=name,
                description="Port with name {}".format(name))
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return updated

    @cache
    def spam_router_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "routers", "name",
                                   lambda x: x == name):
                break

        try:
            log.info("Creating router with name {}".format(name))
            created = self.native.routers.create(
                name=name, description="Router with name {}".format(name))
        except Exception:
            return

        return created

    @uncache
    def spam_router_delete(self):
        routers = self.keeper.get(
            "neutron", "routers", "id",
            lambda x: x in self.cache["neutron"]["routers"])

        if len(routers) > 0:
            router = random.choice(routers)
        else:
            log.warning("There is no routers for removing, skipping...")
            return

        try:
            log.info("Removing router with id {}".format(router.id))
            self.native.routers.delete(router.id)
        except Exception:
            return

        return router.id

    def spam_router_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "routers", "name",
                                   lambda x: x == name):
                break

        routers = self.keeper.get(
            "neutron", "routers", "id",
            lambda x: x in self.cache["neutron"]["routers"])

        if len(routers) > 0:
            router = random.choice(routers)
        else:
            log.warning("There is no routers for updating, skipping...")
            return

        try:
            log.info("Updating router with id {}".format(router.id))
            updated = self.native.routers.update(
                router.id, name=name,
                description="Router with name {}".format(name))
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return updated

    @cache
    def spam_security_group_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "security_groups", "name",
                                   lambda x: x == name):
                break

        try:
            log.info("Creating security group with name {}".format(name))
            created = self.native.security_groups.create(
                name=name,
                description="Security group with name {}".format(name))
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def spam_security_group_delete(self):
        security_groups = self.keeper.get(
            "neutron", "security_groups", "id",
            lambda x: x in self.cache["neutron"]["security_groups"])

        if len(security_groups) > 0:
            security_group = random.choice(security_groups)
        else:
            log.warning("There is no security groups for removing, "
                        "skipping...")
            return

        try:
            log.info(
                "Remove security group with id {}".format(security_group.id))
            self.native.security_groups.delete(security_group.id)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return security_group.id

    def spam_security_group_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "security_groups", "name",
                                   lambda x: x == name):
                break

        security_groups = self.keeper.get(
            "neutron", "security_groups", "id",
            lambda x: x in self.cache["neutron"]["security_groups"])

        if len(security_groups) > 0:
            security_group = random.choice(security_groups)
        else:
            log.warning("There is no security groups for updating, "
                        "skipping...")
            return

        try:
            log.info("Update security group with id".format(security_group.id))
            updated = self.native.security_groups.update(
                security_group.id, name=name,
                description="Security group with name {}".format(name))
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return updated

    @cache
    def spam_subnet_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "subnets", "name",
                                   lambda x: x == name):
                break

        networks = self.keeper.get(
            "neutron", "networks", "id",
            lambda x: x in self.cache["neutron"]["networks"])

        # TO-DO: Make a normal warning logging
        if len(networks) > 0:
            network = random.choice(networks)
        else:
            return

        subnets = [self.keeper.get("neutron", "subnets", "get", None, subnet)
                   for subnet in network.subnets]
        cidr = come_up_subnet(subnets, 2 ** random.randint(3, 4))

        try:
            log.info("Create subnet with name {}".format(name))
            created = self.native.subnets.create(
                cidr=str(cidr), ip_version=4, name=name,
                description="Subnet with name {}".format(name),
                network_id=network.id)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def spam_subnet_delete(self):
        subnets = self.keeper.get(
            "neutron", "subnets", "id",
            lambda x: x in self.cache["neutron"]["subnets"])

        if len(subnets) > 0:
            subnet = random.choice(subnets)
        else:
            log.warning("There is no subnets for removing, skipping...")
            return

        try:
            log.info("Remove subnet with id {}".format(subnet.id))
            self.native.subnets.update(subnet.id)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return subnet.id

    def spam_subnet_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("neutron", "subnets", "name",
                                   lambda x: x == name):
                break

        subnets = self.keeper.get(
            "neutron", "subnets", "id",
            lambda x: x in self.cache["neutron"]["subnets"])

        if len(subnets) > 0:
            subnet = random.choice(subnets)
        else:
            log.warning("There is no subnets for updating, skipping...")
            return

        try:
            log.info("Update subnet with id {}".format(subnet.id))
            updated = self.native.subnets.update(
                subnet.id, name=name,
                description="Subnet with name {}".format(name))
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return updated


class SpamNova(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `SpamNova` class instance.

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
        self.spam.keypairs = lambda: None
        self.spam.servers = lambda: None

        self.spam.flavors.create = self.flavor_create
        self.spam.flavors.delete = self.flavor_delete

        self.spam.keypairs.create = self.keypair_create
        self.spam.keypairs.delete = self.keypair_delete

        self.spam.servers.create = self.server_create
        self.spam.servers.delete = self.server_delete
        self.spam.servers.update = self.server_update

    @cache
    def flavor_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("nova", "flavors", "name",
                                   lambda x: x == name):
                break

        ram_sizes = [256, 512, 1024, 2048, 4096, 8192, 16384]
        vcpus_num = [1, 2, 4, 8]
        volume_sizes = [1, 2, 5, 10, 20, 40, 50, 100, 200, 500]

        try:
            log.info("Creating flavor with name {}".format(name))
            created = self.native.flavors.create(
                name=name, ram=random.choice(ram_sizes),
                vcpus=random.choice(vcpus_num),
                disk=random.choice(volume_sizes))
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def flavor_delete(self):
        flavors = self.keeper.get(
            "nova", "flavors", "id",
            lambda x: x in self.cache["nova"]["flavors"])

        if len(flavors) > 0:
            flavor = random.choice(flavors)
        else:
            log.warning("There is no flavors for removing, skipping")
            return

        try:
            log.info("Removing flavor {}".format(flavor.id))
            self.native.flavors.delete(flavor)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return flavor.id

    @cache
    def keypair_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("nova", "keypairs", "name",
                                   lambda x: x == name):
                break

        key = RSA.generate(2048).publickey().exportKey('OpenSSH')
        try:
            log.info("Creating keypair with name {}".format(name))
            created = self.native.keypairs.create(name=name, public_key=key)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def keypair_delete(self):
        keypairs = self.keeper.get(
            "nova", "keypairs", "id",
            lambda x: x in self.cache["nova"]["keypairs"])
        if len(keypairs) > 0:
            keypair = random.choice(keypairs)
        else:
            log.warning("There is no keypairs for removing, skipping...")

        try:
            log.info("Removing keypair {}".format(keypair.id))
            self.native.keypairs.delete(keypair)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return keypair.id

    @cache
    def server_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("nova", "servers", "name",
                                   lambda x: x == name):
                break

        images = self.keeper.get(
            "glance", "images", "id",
            lambda x: x in self.cache["nova"]["servers"])
        flavors = self.keeper.get(
            "nova", "flavors", "id",
            lambda x: x in self.cache["nova"]["servers"])

        if len(images) > 0 and len(flavors) > 0:
            image = random.choice(images)
            flavor = random.choice(flavors)
        else:
            log.warning("There is no images or flavors for creating server, "
                        "skipping...")
            return

        networks = self.keeper.get("neutron", "networks", None,
                                   (lambda x, y: len(x) > 0 and
                                    y in self.cache["neutron"]["networks"]),
                                   "subnets", "id")

        if len(networks) > 0:
            network = random.choice(networks)
        else:
            log.warning("There is no networks with subnets, skipping "
                        "server creating...")
            return

        try:
            log.info("Creating server with name {}".format(name))
            created = self.native.servers.create(
                name=name, image=image, flavor=flavor,
                nics=[{"net-id": network.id}])
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def server_delete(self):
        servers = self.keeper.get(
            "nova", "servers", "id",
            lambda x: x in self.cache["nova"]["servers"])

        if len(servers) > 0:
            server = random.choice(servers)
        else:
            log.warning("There is no servers for removing, skipping...")
            return

        try:
            log.info("Removing server {}".format(server.id))
            self.native.servers.delete(server)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return server.id

    def server_update(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("nova", "servers", "name",
                                   lambda x: x == name):
                break

        servers = self.keeper.get(
            "nova", "servers", "id",
            lambda x: x in self.cache["nova"]["servers"])

        if len(servers) > 0:
            server = random.choice(servers)
        else:
            log.warning("There is no servers for updating, skipping...")
            return

        try:
            log.info("Updating server {}".format(server.id))
            updated = self.native.servers.update(server=server, name=name)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return updated


class SpamSwift(object):
    def __init__(self, cache, client, faker=None, keeper=None):
        """Create `SpamSwift` class instance.

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

        self.spam.containers = lambda: None
        self.spam.containers.create = self.container_create
        self.spam.containers.delete = self.container_delete

        self.spam.objects = lambda: None
        self.spam.objects.create = self.object_create
        self.spam.objects.delete = self.object_delete

    @cache
    def container_create(self):
        while True:
            name = self.faker.word()
            if not self.keeper.get("swift", "containers", "name",
                                   lambda x: x == name):
                break

        try:
            log.info("Creating container with name {}".format(name))
            created = self.native.containers.create(name)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def container_delete(self):
        containers = self.keeper.get(
            "swift", "containers", "id",
            lambda x: x in self.cache["swift"]["containers"])

        if len(containers) > 0:
            container = random.choice(containers)
        else:
            log.warning("There is no containers for removing, skipping...")
            return

        if container["x-container-object-count"] > 0:
            for object in self.native.objects.list(container):
                self.native.objects.delete(container, object)

        try:
            log.info("Removing container {}".format(container.id))
            self.native.containers.delete(container)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return container.id

    @cache
    def object_create(self):
        containers = self.keeper.get(
            "swift", "containers", "id",
            lambda x: x in self.cache["swift"]["containers"])

        if len(containers) > 0:
            container = random.choice(containers)
        else:
            log.warning("There is no containers for creating object, "
                        "skipping...")
            return

        while True:
            name = self.faker.word()
            if not self.keeper.get("swift", "objects", "name",
                                   lambda x: x == name, list_args=[container]):
                break

        try:
            log.info("Creating object with name {0} in container {1}".
                     format(name, container.name))
            created = self.native.objects.create(container, name,
                                                 self.faker.paragraph())
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return created

    @uncache
    def object_delete(self):
        containers = self.keeper.get(
            "swift", "containers", "id",
            lambda x: x in self.cache["swift"]["containers"])

        if len(containers) > 0:
            container = random.choice(containers)
        else:
            log.warning("There is no containers for deleting object, "
                        "skipping...")
            return

        objects = self.keeper.get(
            "swift", "objects", "id",
            lambda x: x in self.cache["swift"]["objects"],
            list_args=[container])

        if len(objects) > 0:
            object = random.choice(objects)
        else:
            log.warning("There is no objects for removing, skipping...")
            return

        try:
            log.info("Removing object {0} from container {1}".
                     format(object.id, container.id))
            self.native.objects.delete(container, object)
        except Exception as exc:
            log.critical("Exception: {}".format(exc))
            return

        return object.id
