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

import argparse
import collections
import json
import logging

from cache import Cache
from client_factory import ClientFactory
from keeper import Keeper
import logger
from session import Session
from simulator import Simulator


parser = argparse.ArgumentParser()
parser.add_argument('--pipe', dest='pipelines',
                    default='/etc/spamostack/conf.json',
                    help='Path to the config file with pipes')
parser.add_argument('--db', dest='db', default='./db',
                    help='Path to the database directory')
args = parser.parse_args()

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(logger.SpamStreamHandler())


def main():
    if args.pipelines:
        with open(args.pipelines, 'r') as pipes_file:
            pipelines = json.load(pipes_file,
                                  object_pairs_hook=collections.OrderedDict)

    simulators = []
    cache = Cache(args.db)

    admin_session = Session(cache)
    admin_factory = ClientFactory(cache)
    admin_keeper = Keeper(cache, admin_session, admin_factory)

    for pipe_name, pipe in pipelines.iteritems():
        simulators.append(Simulator(pipe_name, pipe, cache, admin_keeper))

    for simulator in simulators:
        simulator.simulate()

if __name__ == "__main__":
    main()
