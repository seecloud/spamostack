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
import sys


from cache import Cache
from client_factory import ClientFactory
import coloredlogs
from keeper import Keeper
import logger
from simulator import Simulator


parser = argparse.ArgumentParser()
parser.add_argument('--conf', dest='conf',
                    default='/etc/spamostack/conf.json',
                    help='Path to the config file with pipes')
parser.add_argument('--db', dest='db', default='./db',
                    help='Path to the database directory')
parser.add_argument('--verbose', action='store_true',
                    help='Increase verbose output')
parser.add_argument('--clean', dest='clean', nargs='+',
                    help='Path to the database directory')
args = parser.parse_args()

log = logging.getLogger()
if args.verbose:
    log.setLevel(logging.DEBUG)
    level = 'DEBUG'
else:
    log.setLevel(logging.INFO)
    level = 'INFO'
log.addHandler(logger.SpamStreamHandler())
coloredlogs.install(level=level)


def main():
    try:
        if args.conf:
            log.info("Reading conf from {}".format(args.conf))
            with open(args.conf, 'r') as pipes_file:
                conf = json.load(pipes_file,
                                 object_pairs_hook=collections.OrderedDict)

        simulators = []
        cache = Cache(args.db)

        admin_user = cache["users"]["admin"]
        admin_user["auth_url"] = cache["api"]["auth_url"]

        admin_factory = ClientFactory(admin_user)
        admin_keeper = Keeper(cache, admin_factory)

        if args.clean:
            log.info("Starting cleanup")
            admin_keeper.clean(args.clean)
            sys.exit()

        # This section for default initialization of cirros image
        log.debug("Caching default cirros image")
        (cache["glance"]["images"]
         [admin_keeper.get(
             "glance", "images", "name",
             lambda x: x == "cirros-0.3.4-x86_64-uec")[0].id]) = False
        for flavor in admin_factory.nova().flavors.list():
            log.debug("Caching flavor with name {name}".
                      format(name=flavor.name))
            (cache["nova"]["flavors"][flavor.id]) = False

        for pipe_name, pipe in conf.iteritems():
            simulators.append(Simulator(pipe_name, pipe, cache, admin_keeper))

        for simulator in simulators:
            simulator.simulate()
    except KeyboardInterrupt:
        print('\nThe process was interrupted by the user')
        raise SystemExit


if __name__ == "__main__":
    main()
