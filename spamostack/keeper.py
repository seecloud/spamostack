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


log = logging.getLogger(__name__)


class Keeper(object):
    def __init__(self, cache, client_factory):
        """Create an instance of `Keeper` class

        @param cahce: Reference to the cache
        @type cache: `spamostack.cache.Cache`

        @param client_factory: Reference to the client factory
        @type client_factory: `client_factory.ClientFactory`
        """

        self.cache = cache
        self.client_factory = client_factory
        self.default_init()

    def default_init(self):
        """Initialize the default admin user."""

        log.debug("Start default initialization for admin user")
        client = getattr(self.client_factory, "keystone")()
        user = client.users.find(name="admin")
        project = client.projects.find(name="admin")
        self.cache["keystone"]["users"][user.id] = False

        # quotas update
        self.client_factory.cinder().quotas.update(
            project.id, backup_gigabytes=-1, backups=-1, gigabytes=-1,
            per_volume_gigabytes=-1, snapshots=-1, volumes=-1)
        self.client_factory.neutron().quotas.update(
            project.id, subnet=-1, network=-1, floatingip=-1, subnetpool=-1,
            port=-1, security_group_rule=-1, security_group=-1, router=-1,
            rbac_policy=-1)
        self.client_factory.nova().quotas.update(
            project.id, cores=-1, fixed_ips=-1, floating_ips=-1,
            injected_file_content_bytes=-1, injected_file_path_bytes=-1,
            injected_files=-1, instances=-1, key_pairs=-1, metadata_items=-1,
            ram=-1, security_group_rules=-1, security_groups=-1,
            server_group_members=-1, server_groups=-1)

    def get(self, client_name, resource_name, param=None, func=None,
            *args, **kwargs):
        """Get a resource.

        If `param` and `func` is not `None` then `param` gets retrieve
        with **kwargs as arguments then passes result to the `func`
        as an argument and if `func` passes as `True`
        then returns it as result.

        If `func` is `None` then `param` gets retrieve with *args, **kwargs and
        returns it as result.

        If `param` is `None` then `func` gets retrieve with *args, **kwargs and
        if `func` passes as `True` then returns it as result.

        If `param` and `func` is `None` then returns a random resource.

        @param client_name: Name of the client
        @type client_name: `str`

        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`

        @param param: A parameter which would be examined
        @type param: `str`

        @param func: A method which would be used to examine a parameter
        @type func: `method`

        @param list_args: Parameter which would be passed to `list` methods.
        Dirty hack:
        That parameter defines in **kwargs but then it will be deleted from it.
        @type list_args: `list`
        """

        if kwargs and "list_args" in kwargs:
            list_args = kwargs["list_args"]
            del kwargs["list_args"]
        else:
            list_args = []

        client = getattr(self.client_factory, client_name)()
        resource = getattr(client, resource_name)
        result = None

        log.info("Trying get info about {resource} from {client}".
                 format(resource=resource_name, client=client_name))
        if func is not None and param is not None:
            result = []
            try:
                for el in list(resource.list(*list_args)):
                    if not args and not kwargs:
                        probe = getattr(el, param)
                    else:
                        probe = getattr(el, param)(*args, **kwargs)

                    if func(probe):
                        result.append(el)
            except Exception as exc:
                log.critical("Exception: {}".format(exc))
                pass
        elif func is None and param is not None:
            try:
                if not args and not kwargs:
                    result = getattr(resource, param)
                else:
                    result = getattr(resource, param)(*args, **kwargs)
            except Exception as exc:
                log.critical("Exception: {}".format(exc))
                pass
        elif func is not None and param is None:
            result = []
            try:
                for el in list(resource.list(*list_args)):
                    params = []
                    for arg in args:
                        params.append(getattr(el, arg))

                    if func(*params):
                        result.append(el)
            except Exception as exc:
                log.critical("Exception: ".format(exc))
                pass
        elif func is None and param is None:
            possibilities = list(resource.list(*list_args))
            if len(possibilities) > 0:
                result = random.choice(possibilities)

        return result

    def clean(self, component_names):
        """Delete all the resources for specific component

        @param component_names: Names of the components that resources
        will be cleared
        @type component_names: `list(str)`
        """

        existing_components = ["cinder", "glance", "keystone", "neutron",
                               "nova"]

        binded_resources = {"neutron":
                            ["subnets", "ports", "routers", "networks"]}

        exceptions = [self.get("keystone", "users", "name",
                               lambda x: x == "admin")[0].id,
                      self.get("keystone", "projects", "name",
                               lambda x: x == "admin")[0].id,
                      self.get("glance", "images", "name",
                               lambda x: x == "cirros-0.3.4-x86_64-uec")[0].id]

        if component_names == ["all"]:
            components = existing_components
        else:
            components = component_names

        for client_name in components:
            log.debug("Start cleaning for {} client".format(client_name))

            client = getattr(self.client_factory, client_name)()

            if client_name in binded_resources:
                resources = binded_resources[client_name]
            else:
                resources = self.cache[client_name].keys()

            for resource_name in resources:
                log.debug("Cleaning {} resource".format(resource_name))
                resource_obj = getattr(client, resource_name)
                for id in self.cache[client_name][resource_name].keys():
                    if id not in exceptions:
                        if resource_name in ["volumes"]:
                            resource_obj.detach(id)
                        try:
                            resource_obj.delete(id)
                        except Exception as exc:
                            raise exc
                    del self.cache[client_name][resource_name][id]
            if client_name == "keystone":
                for key in self.cache["users"].keys():
                    del self.cache["users"][key]
