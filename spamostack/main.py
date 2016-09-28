import argparse
import json

from session import Session
from simulator import Simulator
from cache import Cache
from client_factory import ClientFactory
from keeper import Keeper


parser = argparse.ArgumentParser()
parser.add_argument('--pipe', dest='pipelines', required=True,
                    help='Path to the config file with pipes')
parser.add_argument('--db', dest='db', default='./db',
                    help='Path to the database directory')
args = parser.parse_args()


def main():
    if args.pipelines:
        with open(args.pipelines, 'r') as pipes_file:
            pipelines = json.load(pipes_file)

    simulalators = []
    cache = Cache(args.db)

    admin_session = Session(cache)
    admin_factory = ClientFactory(cache)
    admin_keeper = Keeper(cache, admin_session, admin_factory)

    for pipe_name, pipe in pipelines.iteritems():
        simulalators.append(Simulator(pipe_name, pipe, cache, admin_keeper))

    for simulator in simulalators:
        simulalator.simulate()

if __name__ == "__main__":
    main()
