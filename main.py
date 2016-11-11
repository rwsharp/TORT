import sys
import os.path
import argparse
import datetime
from lib.trail import Trail
from lib.party import Party
from lib.world import World

def main(args):
    trials = 1
    strategy = 'greatest need'
    start_datetime = datetime.datetime.strptime(args.start_date_time, '%Y-%m-%d %H:%M')

    data_path = os.path.abspath('data/')
    trail_file_name = os.path.join(data_path, 'belly_river_trail.json')
    terrain_file_name = os.path.join(data_path, 'belly_river_terrain.json')
    party_file_name = os.path.join(data_path, 'belly_river_party.json')

    for t in range(trials):

        trail = Trail(start_datetime, trail_file_name, terrain_file_name)
        party = Party(start_datetime, party_file_name, trail)
        world = World(start_datetime, party, trail)

        # simulate until destination or death
        continue_trail = True

        while continue_trail:
            world.update(strategy)

            if world.party.condition in ('arrived', 'dead'):
                # update Powell metrics
                continue_trail = False

            print world.date_and_time, world.party.current_stop.mile_marker, world.party.current_stop.name
            print world.party.condition, world.party.number_alive()
            print

    # present Powell metrics

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date-time", help="party start date YYYY-MM-DD hh:mm")
    args = parser.parse_args()
    main(args)