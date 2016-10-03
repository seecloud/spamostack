import time
import leveldb
from random import randint

XRANGE_N = 100000
N = 99999
db = leveldb.LevelDB("./db")
d = dict()

# Write

t = time.time()
for idx in xrange(XRANGE_N):
    d[str(idx)] = randint(0, N)

print("Write time for Dictionary is {}".format(time.time() - t))

t = time.time()
for idx in xrange(XRANGE_N):
    d[str(idx)] = str(randint(0, N))

print("Write time for Dictionary with str is {}".format(time.time() - t))

t = time.time()
for idx in xrange(XRANGE_N):
    db.Put(str(idx), str(randint(0, N)))

print("Write time for LevelDB with str is {}".format(time.time() - t))

# Read

t = time.time()
for idx in xrange(XRANGE_N): 
    d[str(idx)]

print("Read time for Dictionary without eval is {}".format(time.time() - t))

t = time.time()
for idx in xrange(XRANGE_N): 
    eval(d[str(idx)])

print("Read time for Dictionary with eval is {}".format(time.time() - t))

t = time.time()
for idx in xrange(XRANGE_N):
    db.Get(str(randint(0, N)))

print("Read time for LevelDB without eval is {}".format(time.time() - t))

t = time.time()
for idx in xrange(XRANGE_N):
    eval(db.Get(str(randint(0, N))))

print("Read time for LevelDB with eval is {}".format(time.time() - t))
