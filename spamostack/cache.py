from collections import MutableMapping
from collections import defaultdict
import leveldb
import os

from client_factory import ClientFactory


nested_dict = lambda: defaultdict(nested_dict)


class Cache(MutableMapping, object):
    def __init__(self, path='./db'):
        """
        Create instance of `Cache` class

        @param path: Path to the database
        @type path: `str`
        """

        self.db = leveldb.LevelDB(path)
        self.cache = nested_dict()
        self.default_init()
        self.load()

    # Concrete methods for MutableMapping
    def __getitem__(self, key):
        return self.cache[key]

    def __setitem__(self, key, value):
        self.db.Put(key, str(value))
        self.cache[key] = value

    def setdefault(self, key, value=None):
        self.db.Put(key, str(value))
        return self.cache.setdefault(key, value)

    def __delitem__(self, key):
        del self.cache[key]

    def __iter__(self):
        return iter(self.cache)

    def __len__(self):
        return len(self.cache)
    # end

    def default_init(self):
        "Default initialization for cache"

        uname = os.environ['OS_USERNAME']

        self.cache["created"]["users"][uname]['password'] = \
            os.environ['OS_PASSWORD']
        self.cache["created"]["users"][uname]['project_name'] = \
            os.environ['OS_PROJECT_NAME']
        self.cache["auth_url"] = os.environ['OS_AUTH_URL']
        self.cache["created"]["users"][uname]['project_domain_id'] = 'default'
        self.cache["created"]["users"][uname]['user_domain_id'] = 'default'

    def load(self):
        """Load db into cache"""

        def to_objects(cache_elem):
            for key, value in cache_elem.iteritems():
                if isinstance(value, dict):
                    to_objects(value)
                else:
                    try:
                        cache_elem[key] = eval(value)
                    except NameError as exc:
                        cache_elem[key] = value

        for key, value in self.db.RangeIter():
            self.cache[key] = eval(value)
            if key == "created":
                to_objects(self.cache[key])

    def update(self):
        """Update existing db with data from cache"""

        def to_strings(cache_elem):
            for key, value in cache_elem.iteritems():
                if isinstance(value, dict):
                    to_strings(value)
                else:
                    cache_elem[key] = str(value)

        batch = leveldb.WriteBatch()
        for key, value in self.cache.iteritems():
            if key == "created":
                to_strings(self.cache[key])
            self.db.Put(key, str(self.cache[key]))
        self.db.Write(batch, sync=True)
