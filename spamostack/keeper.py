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
        self.cache["keystone"]["users"][user.id] = False

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
                resource[key] = True
                return key

    def get_random(self, resource):
        """Get random resource

        @param resource: Part of the cache
        @type resource: `str`
        """

        return random.choice(resource.keys())

    def clean(self, component_names):
        """Delete all the resources for specific component

        @param component_names: Names of the components that resources
        will be cleared
        @type component_names: `list(str)`
        """

        admin_user_id = self.get_by_name("keystone", "users", "admin").id

        for client_name in component_names:
            client = getattr(self.client_factory, client_name)()
            for resource_name, resource in self.cache[client_name].iteritems():
                resource_obj = getattr(client.client, resource_name)
                for id in resource.keys():
                    if id != admin_user_id:
                        resource_obj.delete(self.get_by_id(client_name,
                                                           resource_name, id))
                    del self.cache[client_name][resource_name][id]
            if client_name == "keystone":
                for key in self.cache["users"].keys():
                    del self.cache["users"][key]
