import sys
import os.path
from lib.trail import Trail
from lib.party import Party

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

        # simulate until destination or death
        continue_trail = True

        while continue_trail:
            # make decisions
            action = party.decide(strategy)
            # update state based on action
            print 'action: ' + str(action)
            party.update(action)

            if party.condition in ('arrived', 'dead'):
                # update Powell metrics
                continue_trail = False

            print party.date, party.current_stop.mile_marker, party.current_stop.name 
            print party.condition, party.number_alive()
            print party.inventory
            #print party.members[0]
            print

    # present Powell metrics

if __name__ == '__main__':
    main()