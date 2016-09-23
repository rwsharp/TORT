import json
from datetime import datetime, timedelta

class Trail():
    """
    Defines the trail and simulates a party travelling it.
    """
    def __init__(self, trail_file_name=None):
        if trail_file_name is not None:
            with open(trail_file_name, 'r') as trail_file:
                self.stops = json.load(trail_file)
                self.set_mile_markers()
        else:
            self.stops = None

        self.date = datetime.strptime('1846-03-01', '%Y-%m-%d')


    def set_date(self, date):
        self.date = date


    def next_stop(self, current_mile_marker):
        next_stop = None
        for i, stop in enumerate(self.stops):
            if stop['mile marker'] > current_mile_marker:
                next_stop = stop
                break

        return next_stop


    def set_mile_markers(self):
        mile_marker = 0

        for i, stop in enumerate(self.stops):
            if stop.get('mile marker') is None:
                if stop.get('miles beyond last marker') is None:
                     raise KeyError('ERROR - This stop on the trail has no location data: ' + str(stop))
                else:
                    mile_marker += stop.get('miles beyond last marker')
                    self.stops[i]['mile marker'] = mile_marker
            else:
                mile_marker = stop.get('mile marker')

            if i > 0:
                if stop['mile marker'] <= self.stops[i-1]['mile marker']:
                    raise ValueError('ERROR - List of trail stops is out of order.')


    def start_of_trail(self):
        return self.stops[0]

    def end_of_trail(self):
        return self.stops[-1]


    def update(self, party, action):
        if action['type'] == 'travel':
            self.travel(party, action['parameters'])
        else:
            raise ValueError('ERROR - Action not recognized: ' + str(action))

        return party.state()


    def travel(self, party, parameters):
        """
        Simulate one day's travel along the trail. Update's the condition of the party.

        Parameters
        ----------
        party: the party traveling the trail

        Returns
        -------
        """

        miles_per_day = party.get_min_speed()

        if party.data['mile marker'] + miles_per_day >= party.next_stop['mile marker']:
            # arrived at next stop
            print 'Arrived at ' + party.next_stop['name']
            party.data['mile marker'] = party.next_stop['mile marker']
            party.last_stop = party.next_stop
            party.next_stop = self.next_stop(party.data['mile marker'])
        else:
            party.data['mile marker'] += miles_per_day

        party.feed()
        party.update_health()
        self.date += timedelta(days=1)

        return
