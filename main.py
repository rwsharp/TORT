import sys
import os.path
from lib.trail import Trail
from lib.party import Party
from lib.world import World

def main():
    trials = 1
    strategy = 'greatest need'

    data_path = os.path.abspath('data/')
    trail_file_name = os.path.join(data_path, 'belly_river_route.json')
    terrain_file_name = os.path.join(data_path, 'belly_river_terrain.json')
    party_file_name = os.path.join(data_path, 'belly_river_party.json')

    for t in range(trials):

        trail = Trail(trail_file_name, terrain_file_name)
        party = Party(party_file_name, trail)
        world = World(party = party, trail = trail, dt = party.start_datetime)

        # simulate until destination or death
        continue_trail = True

        while continue_trail:
            world.update(strategy)

            if world.party.condition in ('arrived', 'dead'):
                # update Powell metrics
                continue_trail = False

            print world.party.date, world.party.current_stop.mile_marker, world.party.current_stop.name
            print world.party.condition, world.party.number_alive()
            print world.party.inventory
            print

    # present Powell metrics

if __name__ == '__main__':
    main()