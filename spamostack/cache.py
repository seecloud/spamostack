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

import collections
import os

import leveldb

nested_dict = lambda: collections.defaultdict(nested_dict)


class LevelCache(collections.MutableMapping, object):
    def __init__(self, path="./db"):
        self.path = path
        self.db = leveldb.LevelDB(self.path)
        self.data = dict()
        self.load()

    # Concrete methods for MutableMapping
    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.db.Put(key, str(value))
        self.data[key] = value

    def setdefault(self, key, value=None):
        self.db.Put(key, str(value))
        return self.data.setdefault(key, value)

    def __delitem__(self, key):
        self.db.Delete(key)
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)
    # end

    def keys(self):
        return self.data.keys()

    def load(self):
        """Load db into cache."""

        for key, value in self.db.RangeIter():
            try:
                self.data[key] = eval(value)
            except NameError:
                self.data[key] = value

    def update(self):
        """Update existing db with data from cache."""

        batch = leveldb.WriteBatch()
        for key, value in self.data.iteritems():
            self.db.Put(key, str(self.data[key]))
        self.db.Write(batch, sync=True)


class Cache(collections.MutableMapping, object):
    def __init__(self, path='./db'):
        """Create instance of `Cache` class

        @param path: Path to the database
        @type path: `str`
        """

        self.cache = nested_dict()
        self.path = path
        self.default_init()

    # Concrete methods for MutableMapping
    def __getitem__(self, key):
        return self.cache[key]

    def __setitem__(self, key, value):
        self.cache[key] = value

    def setdefault(self, key, value=None):
        return self.cache.setdefault(key, value)

    def __delitem__(self, key):
        del self.cache[key]

    def __iter__(self):
        return iter(self.cache)

    def __len__(self):
        return len(self.cache)
    # end

    def default_init(self):
        """Default initialization for cache."""

        uname = os.environ['OS_USERNAME']
        self.cache["created"]["users"][uname]) = LevelCache(
            os.path.join(self.path, "created","users", uname))

        self.cache["created"]["users"][uname]['password'] = \
            os.environ['OS_PASSWORD']

        (self.cache["created"]["users"]
         [uname]['password']) = os.environ['OS_PASSWORD']

        (self.cache["created"]["users"]
         [uname]['password']) = os.environ['OS_PASSWORD']
        (self.cache["created"]["users"]
         [uname]['project_name']) = os.environ['OS_PROJECT_NAME']
        self.cache["auth_url"] = os.environ['OS_AUTH_URL']
        self.cache["created"]["users"][uname]['project_domain_id'] = 'default'
        self.cache["created"]["users"][uname]['user_domain_id'] = 'default'

        self.cache["identity"]["projects"] = LevelCache(
            os.path.join(self.path, "identity", "projects"))

        self.cache["identity"]["users"] = LevelCache(
            os.path.join(self.path, "identity", "users"))

        self.cache["volume"]["volumes"] = LevelCache(
            os.path.join(self.path, "volume", "volumes"))
