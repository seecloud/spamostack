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
    def __init__(self, cache, session, client_factory):
        """Create an instance of `Keeper` class

        @param cahce: Reference to the cache
        @type cache: `spamostack.cache.Cache`
        @param session: Reference to the session
        @type session: `session.Session`
        @param client_factory: Reference to the client factory
        @type client_factory: `client_factory.ClientFactory`
        """

        self.cache = cache
        self.session = session
        self.client_factory = client_factory
        self.default_init()

    def default_init(self):
        """Initialize the default admin user."""

        client = getattr(self.client_factory, "keystone")(self.session)
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

        client = getattr(self.client_factory, client_name)(self.session)
        resource = getattr(client, resource_name)

        return getattr(resource, "get")(id)

    def get_unused(self, client_name, resource_name):
        """Get unused resource

        @param client_name: Name of the client
        @type client_name: `str`
        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`
        """

        for key, value in self.cache[client_name][resource_name]:
            if value is False:
                self.cache[client_name][resource_name][key] = True
                return self.get_by_id(client_name, resource_name, key)

    def get_random(self, client_name, resource_name):
        """Get random resource

        @param client_name: Name of the client
        @type client_name: `str`
        @param resource_name: Name of the resource under specific component
        @type resource_name: `str`
        """

        return self.get_by_id(client_name, resource_name,
                              random.choice(self.cache[client_name]
                                            [resource_name].keys()))
