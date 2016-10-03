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
import threading
import time

from client_factory import ClientFactory


def threader(func):
    def wrapper(self, *args, **kwargs):
        threading.Thread(target=func, args=(self,)).start()

    return wrapper


class Simulator(object):
    def __init__(self, name, pipeline, cache, keeper):
        """Create an instance of `Simulator` class

        @param name: Name of the pipeline
        @type name: `str`
        @param pipeline: Pipeline to be executed
        @type pipeline: `dict`
        @param cahce: Reference to the cache
        @type cache: `spamostack.cache.Cache`
        @param keeper: Reference to the keeper
        @type keeper: `keeper.Keeper`
        """

        self.name = name
        self.pipeline = pipeline
        self.cache = cache
        self.keeper = keeper
        unused_id = self.keeper.get_random(self.cache["keystone"]["users"])
        self.user = self.keeper.get_by_id("keystone", "users", unused_id)
        self.client_factory = ClientFactory(self.cache, self.user, self.keeper)

    @threader
    def simulate(self):
        """Simulate an actions."""

        def loop(pipe_client, pipe, parent_obj):
            for key, value in pipe.iteritems():
                attr = getattr(parent_obj, key)

                if isinstance(value, dict):
                    loop(pipe_client, value, attr)
                else:
                    self.rotate(attr, *value)

        for pipe_client, pipe in self.pipeline.iteritems():
            client = getattr(self.client_factory, pipe_client)()
            loop(pipe_client, pipe, client)

    def rotate(self, func, period, number, count):
        """Execute method specific number of times

        in the period and repeat it specific number of times.

        @param func: Method to be executed
        @type func: `method`
        @param period: Time line to execute the method
        @type period: `int`
        @param number: Number of executes
        @type number: `int`
        @param count: Number of repeats that period
        @type count: `int`
        """

        for cycle in xrange(count):
            for execute in xrange(number):
                func()
                time.sleep(random.randint(0, period / number))
