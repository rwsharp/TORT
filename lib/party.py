import json
from datetime import datetime, timedelta

class Party():
    """
    Defines the trail and simulates a party travelling it.
    """
    def __init__(self, party_file_name=None, trail=None):
        if party_file_name is not None:
            with open(party_file_name, 'r') as party_file:
                self.data = json.load(party_file)

            self.data['start date'] = datetime.strptime(self.data['start date'], '%Y-%m-%d')

        else:
            self.data = None

        if trail is not None:
            self.destination = trail.end_of_trail() # representaed as trail stop
        else:
            self.trail = None

        self.last_stop = trail.start_of_trail()
        self.next_stop = trail.next_stop(self.last_stop['mile marker'])


    def set_destination(self, mile_marker):
        self.destination = mile_marker


    def number_alive(self):
        return sum([1 if member['condition']['health'] > 0 else 0 for member in self.data['members']])


    def decide(self, strategy):
        """
        Make decisions according to the current strategy. Update the party according to the outcome of the decisions.

        Returns: action to take (travel (pace), cross river (method), trade (to buy, to sell), hunt, rest (length),
        repair, replace)
        -------

        """

        if strategy == 'biggest need':
            action = self.decide_biggest_need()

        return action


    def decide_biggest_need(self):
        action = {'type': 'travel',
                  'parameters': {'pace': 'normal'}}

        return action


    def get_min_speed(self):

        min_speed = min([member['abilities']['speed'] for member in self.data['members'] if member['condition']['health'] > 0])

        return min_speed


    def arrived(self):
        return True if self.data['mile marker'] >= self.destination['mile marker'] else False


    def state(self):

        if self.number_alive() == 0:
            state = 'dead'
        elif self.arrived():
            # it's implicit here that number_alive > 0
            state = 'arrived'
        else:
            state = 'on the trail'

        return state


    def feed(self):
        for i, member in enumerate(self.data['members']):
            ration = min(member['needs']['food'], self.data['inventory']['food'])
            self.data['inventory']['food'] -= ration

            if 0 < ration < member['needs']['food']:
                severity = -5
            elif ration == 0:
                severity = -10
            else:
                severity = 0

            self.data['members'][i]['condition'].setdefault('afflictions', dict())
            self.data['members'][i]['condition']['afflictions']['hunger'] = severity


    def update_health(self):
        for i, member in enumerate(self.data['members']):
            for affliction, severity in member['condition'].get('afflictions', dict()).iteritems():
                self.data['members'][i]['condition']['health'] += severity
                if self.data['members'][i]['condition']['health'] <= 0:
                    print member['name'] + ' has died of ' + affliction


