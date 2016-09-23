import time
from random import randint
import threading
from collections import OrderedDict

from common import CommonMethods
from client_factory import ClientFactory
from session import Session


def threader(func):
    def wrapper(self, *args, **kwargs):
        threading.Thread(target=func, args=(*args, **kwargs)).start()


class Simulator(CommonMethods, object):
    def __init__(self, name, pipeline, cache):
        super(CommonMethods, self).__init__(cache)

        self.name = name
        self.pipeline = pipeline
        self.cache = cache
        self.client_factory = ClientFactory(cache)
        self.session = Session(cache)

    @threader
    def simulate(self):
        """Simulate an actions"""

        def loop(pipe_client, pipe, parent_obj):
            for key, value in pipe.iteritems():
                attr = getattr(parent_obj, key)

                if isinstance(value, dict):
                    loop(pipe_client, value, attr)
                else:
                    self.rotate(pipe_client, attr, *value)

        for pipe_client, pipe in self.pipeline.iteritems():
            client = getattr(self.client_factory, pipe_client)(self.session)
            loop(pipe_client, pipe, client)

    def rotate(self, name, func, period, number, count):
        """
        Execute method specific number of times in the period and repeat it
        specific number of times.

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
                self.execute(name, func)
                time.sleep(randint(0, period / number))
