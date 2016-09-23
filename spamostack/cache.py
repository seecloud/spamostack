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

    def load(self):
        """Load db into cache"""
	def loop(pipe):
            for key, value in pipe.iteritems():

                if isinstance(value, dict):
                    loop(value)
                else:
                    CommonMethods().

        for key, value in self.db.RangeIter():
            loop(value)
		
            self.cache[key] = eval(value)

    def update(self):
        """Update existing db with data from cache"""

        batch = leveldb.WriteBatch()
        for key, value in self.cache.iteritems():
            self.db.Put(key, str(value))
        self.db.Write(batch, sync=True)
