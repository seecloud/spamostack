import leveldb
from common import CommonMethods

class Cache(object):
    def __init__(self, path='./db'):
        """
        Create instance of `Cache` class

        @param path: Path to the database
        @type path: `str`
        """

        self.db = leveldb.LevelDB(path)
        self.cache = dict()
        self.load()

    def convert_str_to_obj(self, name, cache_elem):
        """

        :param name:
        :param cache_elem:
        :return:
        """
        client = getattr(self.client_factory, name)
        for i in cache_elem.split(','):
            if i.startswith("id="):
                idx = i.split('=')[1]

        obj = client.get(id=idx)

        return obj

    def load(self):
        """Load db into cache"""
	def loop(tasks, name):
            for key, value in tasks.iteritems():
                if isinstance(value, dict):
                    loop(value, name)
                else:
                    tasks[key] = [convert_str_to_obj(name, el) for el in value]

        for key, value in self.db.RangeIter():
            loop(eval(value), key)

    def update(self):
        """Update existing db with data from cache"""

        batch = leveldb.WriteBatch()
        for key, value in self.cache.iteritems():
            self.db.Put(key, str(value))
        self.db.Write(batch, sync=True)
