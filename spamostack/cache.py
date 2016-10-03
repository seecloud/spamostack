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
        try:
            self.db.Get(key)
        except KeyError:
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

        if not os.path.exists(self.path):
            os.mkdir(self.path)
        uname = os.environ['OS_USERNAME']
        self.cache["users"] = LevelCache(
            os.path.join(self.path, "users"))

        admin_user = {"os_username":
                      os.environ['OS_USERNAME'],
                      "os_password":
                      os.environ['OS_PASSWORD'],
                      "os_project_name":
                      os.environ['OS_PROJECT_NAME'],
                      "os_auth_url":
                      os.environ['OS_AUTH_URL'],
                      "os_project_domain_id":
                      os.environ['OS_PROJECT_DOMAIN_ID'],
                      "os_user_domain_id":
                      os.environ['OS_USER_DOMAIN_ID']}
        self.cache["users"][uname] = admin_user

        self.cache["api"] = {"os_compute_api_version":
                             os.environ['OS_COMPUTE_API_VERSION'],
                             "os_identity_api_version":
                             os.environ['OS_IDENTITY_API_VERSION'],
                             "os_image_api_version":
                             os.environ['OS_IMAGE_API_VERSION'],
                             "os_network_api_version":
                             os.environ['OS_NETWORK_API_VERSION'],
                             "os_volume_api_version":
                             os.environ['OS_VOLUME_API_VERSION']}

        keystone_path = os.path.join(self.path, "keystone")
        if not os.path.exists(keystone_path):
            os.mkdir(keystone_path)
        self.cache["keystone"]["projects"] = LevelCache(
            os.path.join(keystone_path, "projects"))

        self.cache["keystone"]["users"] = LevelCache(
            os.path.join(self.path, "keystone", "users"))

        cinder_path = os.path.join(self.path, "cinder")
        if not os.path.exists(cinder_path):
            os.mkdir(cinder_path)
        self.cache["cinder"]["volumes"] = LevelCache(
            os.path.join(cinder_path, "volumes"))
