import os.path
from lib.trail import Trail
from lib.party import Party

def main():
    trials = 1
    strategy = 'biggest need'

    data_path = os.path.abspath('data/')
    trail_file_name = os.path.join(data_path, 'route.json')
    party_file_name = os.path.join(data_path, 'party.json')

    for t in range(trials):

        trail = Trail(trail_file_name)
        party = Party(party_file_name, trail)
        trail.set_date(party.data['start date'])

        # simulate until destination or death
        continue_trail = True

        while continue_trail:
            # make decisions
            action = party.decide(strategy)
            # travel 1 day / update conditions
            party_state = trail.update(party, action)

            if party_state in ('arrived', 'dead'):
                # update Powell metrics
                continue_trail = False

            print trail.date, party.data['mile marker'], party_state, party.number_alive()
            print party.data['inventory']
            print party.data['members'][0]
            print

    # present Powell metrics

if __name__ == '__main__':
    main()