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

import random


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

    def get_by_id(self, client_name, resource_name, id):
        """Get resource by id

        @param client_name: Name of the client
        @type client_name: `str`

        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`

        @param id: ID of the resource
        @type id: `str`
        """

        client = getattr(self.client_factory, client_name)()
        resource = getattr(client, resource_name)
        found = None
        try:
            found = getattr(resource, "get")(id)
        except Exception:
            pass
        finally:
            return found

    def get_by_name(self, client_name, resource_name, name):
        """Get resource by name

        @param client_name: Name of the client
        @type client_name: `str`

        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`

        @param name: Name of the resource
        @type name: `str`
        """

        client = getattr(self.client_factory, client_name)()
        resource = getattr(client, resource_name)
        found = None
        try:
            found = getattr(resource, "find")(name=name)
        except Exception:
            pass
        finally:
            return found

    def get_unused(self, resource):
        """Get unused resource

        @param resource: Part of the cache
        @type resource: `str`
        """

        for key, value in resource.iteritems():
            if value is False:
                return key

    def get_used(self, resource):
        """Get used resource

        @param resource: Part of the cache
        @type resource: `str`
        """

        for key, value in resource.iteritems():
            if value is True:
                return key

    def get_random(self, resource):
        """Get random resource

        @param resource: Part of the cache
        @type resource: `str`
        """

        if len(resource.keys()) == 0:
            return

        return random.choice(resource.keys())

    def get(self, client_name, resource_name, param=None, func=None, **kwargs):
        """Get a resource.

        If `param` and `func` is not `None` then `param` gets retrieve
        with **kwargs as arguments then passes result to the `func`
        as an argument and then returns it as result.

        If `func` is `None` then `param` gets retrieve with **kwargs and
        returns it as result.

        If `param` is `None` then returns a random resource.

        @param client_name: Name of the client
        @type client_name: `str`

        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`

        @param param: A parameter which would be examined
        @type param: `str`

        @param func: A method which would be used to examine a parameter
        @type func: `method`
        """

        client = getattr(self.client_factory, client_name)()
        resource = getattr(client, resource_name)
        result = None

        if func is not None and param is not None:
            try:
                for el in list(resource.list()):
                    if not kwargs:
                        probe = getattr(el, param)
                    else:
                        probe = getattr(el, param)(**kwargs)
                    if func(probe):
                        result = el
                        break
            except Exception:
                pass
        elif func is None and param is not None:
            try:
                result = getattr(resource, param)(**kwargs)
            except Exception:
                pass
        elif param is None:
            possibilities = list(resource.list())
            if len(possibilities) > 0:
                result = random.choice(possibilities)

        return result

    def clean(self, component_names):
        """Delete all the resources for specific component

        @param component_names: Names of the components that resources
        will be cleared
        @type component_names: `list(str)`
        """

        admin_user_id = self.get_by_name("keystone", "users", "admin").id

        for client_name in component_names:
            client = getattr(self.client_factory, client_name)()
            for resource_name, resource in reversed(list(
                    self.cache[client_name].iteritems())):
                resource_obj = getattr(client, resource_name)
                for id in reversed(resource.keys()):
                    if id != admin_user_id:
                        try:
                            resource_obj.delete(id)
                        except Exception as exc:
                            raise exc
                    del self.cache[client_name][resource_name][id]
            if client_name == "keystone":
                for key in self.cache["users"].keys():
                    del self.cache["users"][key]
