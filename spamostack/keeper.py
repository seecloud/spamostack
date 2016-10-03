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

        return getattr(resource, "get")(id)

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

        return getattr(resource, "find")(name=name)

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
