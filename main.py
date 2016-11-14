import sys
import os.path
import argparse
import datetime
from lib.trail import Trail
from lib.party import Party
from lib.world import World

from numpy import mean

def main(args):
    trials = 1000
    strategy = 'greatest need'
    start_datetime = datetime.datetime.strptime(args.start_date_time, '%Y-%m-%d %H:%M')

    data_path = os.path.abspath('data/')
    trail_file_name = os.path.join(data_path, 'belly_river_trail.json')
    terrain_file_name = os.path.join(data_path, 'belly_river_terrain.json')
    party_file_name = os.path.join(data_path, 'belly_river_party.json')

    stats = {'survivors': list(),
             'travel time': list(),
             'bear attacks': list()}

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

            #print world.date_and_time, world.party.current_stop.mile_marker, world.party.current_stop.name
            #print world.party.condition, world.party.number_alive()
            #world.party.print_party_status()
            #print
        stats['travel time'].append((world.date_and_time - start_datetime).total_seconds())
        stats['survivors'].append(world.party.number_alive())
        stats['bear attacks'].append(world.event_counter['bear attack'].get(True, 0))

    #print 'Total trail time:', world.date_and_time - start_datetime

    print 'number of trips:', len(stats['survivors'])
    print 'number of bear attacks', sum(stats['bear attacks'])
    print 'mean survivors:', mean(stats['survivors'])
    print 'mean travel time (h):', mean(stats['travel time'])/60.0/60.0

    # present Powell metrics
    bears_per_mile = sum(stats['bear attacks']) / 25.67 / trials
    mortality = (4.0*trials - sum(stats['survivors'])) / trials
    powells = 1.25 * (25.67 + 4495 / 1000) * (mortality * 2) * 1000.0
    HARM = powells / 25.67

    print bears_per_mile, powells, HARM


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date-time", help="party start date YYYY-MM-DD hh:mm")
    args = parser.parse_args()
    main(args)