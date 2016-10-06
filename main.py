import sys
import os.path
from lib.trail import Trail
from lib.party import Party

def main():
    trials = 1
    strategy = 'greatest need'

    data_path = os.path.abspath('data/')
    trail_file_name = os.path.join(data_path, 'route.json')
    terrain_file_name = os.path.join(data_path, 'terrain.json')
    party_file_name = os.path.join(data_path, 'party.json')

    for t in range(trials):

        trail = Trail(trail_file_name, terrain_file_name)
        party = Party(party_file_name, trail)

        # simulate until destination or death
        continue_trail = True

        while continue_trail:
            # make decisions
            action = party.decide(strategy)
            # update state based on action
            party.update(action)

            if party.condition in ('arrived', 'dead'):
                # update Powell metrics
                continue_trail = False

            print party.date, party.data['mile marker'], party.condition, party.number_alive()
            print party.data['inventory']
            #print party.data['members'][0]
            print

    # present Powell metrics

if __name__ == '__main__':
    main()