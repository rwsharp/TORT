import json
from util import *
from datetime import datetime, timedelta
from stop import Stop
from camp import Camp
from river import River
from town import Town

from numpy import ceil
from numpy.random import uniform, normal


class Party():
    """
    Defines the trail and simulates a party travelling it.
    """
    def __init__(self, party_file_name=None, trail=None):
        if party_file_name is not None:
            with open(party_file_name, 'r') as party_file:
                self.party_data = json.load(party_file)

            self.date = datetime.strptime(self.party_data['start date'], '%Y-%m-%d')

        else:
            raise ValueError('ERROR - party config file required to initialize party.')

        if trail is not None:
            self.trail = trail
            self.destination = trail.end_of_trail()
            # initialize the rivers now that we have a date
            for stop in self.trail.path:
                if isinstance(stop, River):
                    stop.initialize_river_state(self.date.year)

        else:
            raise ValueError('ERROR - trail object required to initialize party.')

        self.members = self.party_data['members']
        self.inventory = self.party_data['inventory']

        self.current_stop = trail.start_of_trail()
        self.last_major_stop = self.current_stop
        self.next_major_stop = trail.next_major_stop(self.last_major_stop.mile_marker)

        self.pace = 'normal'

        self.update_condition()


    def decide(self, strategy):
        """
        Make decisions according to the current strategy. Update the party according to the outcome of the decisions.

        Returns: action to take (travel (pace), cross river (method), trade (to buy, to sell), hunt, rest (length),
        repair, replace)
        -------

        """

        try:
            strategies = {'greatest need': self.decide_greatest_need}
        except KeyError:
            raise ValueError('ERROR - requested strategy is not implemented: ' + str(strategy))

        return strategies[strategy]()


    def decide_greatest_need(self):
        available_actions = self.current_stop.actions

        # party needs are a balance between continue and survive
        # party high level needs are: continue and recover/resupply
        # continue actions: travel/ferry/ford/caulk
        # recover actions: rest/eat/drink/repair/trade/shop/hunt

        max_action, max_utility = None, None
        for action in available_actions:
            if action == 'travel':
                utility = self.utility_travel()
            elif action == 'ford':
                utility = self.utility_ford()
            elif action == 'caulk':
                utility = self.utility_caulk()
            else:
                # we haven't implemented this yet
                utility = None

            if utility is not None:
                if max_utility is None:
                    max_action, max_utility = action, utility
                elif utility > max_utility:
                    max_action, max_utility = action, utility

        if max_action is None:
            raise ValueError('ERROR - No action has a defined utility, connot continue.')

        return max_action


    def utility_travel(self):
        # conversion factors
        # the benefit of travelling 15 miles in a day is equal to the cost of having 3 days left of both food and health
        a = 1.0/15.0
        b = 3.1/2.0

        # nominal distance traveled in one day
        benefit = self.party_speed()
        # cost terms are both in number of days of remaining, so no need for yet another conversion factor
        # cost is geometric sum because 0 is very bad and large values are good
        parameters = {'days': 1}
        cost = 1.0/float(0.1 + self.remaining_food(action='travel', parameters=parameters)) + 1.0/float(0.1 + self.remaining_health(action='travel', parameters=parameters))
        return a*benefit - b*cost


    def utility_ford(self):
        # conversion factors
        # the benefit of crossing the river in a day is equal to the cost of having 3 days left of both food and health
        a = 1.0
        b = 3.1/2.0

        # fording a river runs the risk of a) failure - being forced to go back or b) loss of provisions

        # expected distance traveled in one day
        benefit = 1.0 * self.current_stop.ford_failure_rate(self.date)
        # cost terms are both in number of days of remaining, so no need for yet another conversion factor
        # cost is geometric sum because 0 is very bad and large values are good
        expected_food_loss = self.current_stop.ford_food_loss_fraction(self.date) * self.inventory['food']
        parameters = {'lost food': expected_food_loss}
        cost = 1.0/float(0.1 + self.remaining_food(action='ford', parameters=parameters)) + 1.0/float(0.1 + self.remaining_health(action='ford', parameters=parameters))
        return a*benefit - b*cost


    def utility_caulk(self):
        # conversion factors
        # the benefit of crossing the river in a day is equal to the cost of having 3 days left of both food and health
        a = 1.0
        b = 3.1/2.0

        # caulking and floating across a river runs the risk of a) failure - being forced to go back or b) loss of provisions

        # expected distance traveled in one day
        benefit = 1.0 * self.current_stop.caulk_failure_rate(self.date)
        # cost terms are both in number of days of remaining, so no need for yet another conversion factor
        # cost is geometric sum because 0 is very bad and large values are good
        expected_food_loss = self.current_stop.caulk_food_loss_fraction(self.date) * self.inventory['food']
        parameters = {'lost food': expected_food_loss}
        cost = 1.0/float(0.1 + self.remaining_food(action='ford', parameters=parameters)) + 1.0/float(0.1 + self.remaining_health(action='ford', parameters=parameters))
        return a*benefit - b*cost



    def remaining_food(self, action, parameters):
        # the estiamted amount of food remaining in terms of days remaining after the given action is carried out
        if action == 'travel':
            total_need = sum([member['needs']['food'] for member in self.members if member['condition']['health'] > 0])
            remaining_food = self.inventory['food'] - parameters['days'] * total_need
            remaining_days = remaining_food / float(total_need)
        elif action == 'ford':
            days = 1
            total_need = sum([member['needs']['food'] for member in self.members if member['condition']['health'] > 0])
            remaining_food = self.inventory['food'] - days * total_need - parameters.get('lost food', 0)
            remaining_days = remaining_food / float(total_need)
        else:
            raise ValueError('ERROR - action not implemented: ' + str(action))

        return max(remaining_days, 0.0)


    def feed(self):
        for i, member in enumerate(self.members):
            if member['condition']['health'] > 0:
                ration = min(member['needs']['food'], self.inventory['food'])
                self.inventory['food'] -= ration
    
                if 0 < ration < member['needs']['food']:
                    severity = -5
                elif ration == 0:
                    severity = -10
                else:
                    severity = 0
    
                self.members[i]['condition'].setdefault('afflictions', dict())
                self.members[i]['condition']['afflictions']['hunger'] = severity


    def remaining_health(self, action, parameters):
        member_health = []
        total_severity = []

        for i, member in enumerate(self.members):
            # only count values for living members
            if member['condition']['health'] > 0:
                sev = 0
                for affliction, severity in member['condition'].get('afflictions', dict()).iteritems():
                    sev += severity
    
                total_severity.append(sev)
    
                if action == 'travel':
                    member_health.append(self.members[i]['condition']['health'] + (parameters['days'] * sev))
                elif action == 'ford':
                    days = 1
                    member_health.append(self.members[i]['condition']['health'] + (days * sev))
                else:
                    raise ValueError('ERROR - action not implemented: ' + str(action))
            
        remaining_days = [(100 if s == 0 else h/float(s)) for h, s in zip(member_health, total_severity)]

        return max(min(remaining_days), 0.0)


    def update_health(self):
        for i, member in enumerate(self.members):
            if member['condition']['health'] > 0:
                for affliction, severity in member['condition'].get('afflictions', dict()).iteritems():
                    self.members[i]['condition']['health'] += severity
                    if self.members[i]['condition']['health'] <= 0:
                        print member['name'] + ' has died of ' + affliction
                        # update needs
                        for need in member['needs']:
                            self.members[i]['needs'][need] = 0
    

    def update(self, action):
        if action == 'travel':
            self.travel()
        elif action == 'ford':
            self.ford()
        elif action == 'caulk':
            self.caulk()
        else:
            raise ValueError('ERROR - Action not recognized: ' + str(action))

        self.update_condition()

        return self.condition


    def set_destination(self, mile_marker):
        self.destination = mile_marker


    def number_alive(self):
        return sum([1 if member['condition']['health'] > 0 else 0 for member in self.members])


    def party_speed(self):
        # the party can only travel as fast as its slowest member

        min_speed = min([member['abilities']['speed'] for member in self.members if member['condition']['health'] > 0])

        if self.pace == 'normal':
            pace_modifier = 1.0
        elif self.pace == 'easy':
            pace_modifier = 0.75
        elif self.pace == 'hard':
            pace_modifier = 1.25
        else:
            raise ValueError('ERROR - Unknown pace: ' + str(self.pace))

        travel_speeds = self.current_stop.properties.get('travel speed modifier')
        if travel_speeds is not None:
            terrain_modifier = travel_speeds[date_to_season(self.date)]
        else:
            terrain_modifier = 1.0

        return int(ceil(pace_modifier * terrain_modifier * min_speed))


    def arrived(self):
        return True if self.current_stop.mile_marker >= self.destination.mile_marker else False


    def update_condition(self):

        if self.number_alive() == 0:
            self.condition = 'dead'
        elif self.arrived():
            # it's implicit here that number_alive > 0
            self.condition = 'arrived'
        else:
            self.condition = 'on the trail'


    def travel(self):
        """
        Simulate one day's travel along the trail. Update the condition of the party.

        Returns
        -------
        """

        miles_per_day = self.party_speed()

        # simulate each mile of travel until we either hit a major stop or encounter a calamity
        for i in range(miles_per_day):
            mile_marker = self.current_stop.mile_marker
            self.current_stop = self.trail.path[mile_marker + 1]           

            # todo: decide if a calamity is encountered and the consquences
            for danger in self.current_stop.properties['dangers']:
                if uniform() < danger['probability']:
                    # mon dieu! Disaster strikes!
                    print 'Gadzooks, disaster has struck!'
                    print 'Bad news, it\'s a ' + danger['name']
                    # todo: pick a random victim
                    mu, sig = danger['severity']
                    severity = int(round(normal(mu, sig)))
                    # todo: apply severity
                    # todo: decide if this persists (affliction)
                    # todo: delay the party

            if isinstance(self.current_stop, (River, Town)):
                # arrived at next major stop
                print 'Arrived at ' + self.current_stop.name
                if isinstance(self.current_stop, River):
                    print 'River conditions (width, depth) = ' + str(self.current_stop.river_state(self.date))
                self.last_major_stop = self.current_stop
                self.next_major_stop = self.trail.next_major_stop(self.current_stop.mile_marker)    
                break


        self.feed()
        self.update_health()
        self.date += timedelta(days=1)

        return


    def ford(self):
        """
        Simulate fording a river. It takes one day. Update the condition of the party.

        Returns
        -------
        """

        # fording can fail in which case the party does not advance and loses 1 day of food
        # fording can cause food to get wet and be considered lost
        # fording can succeed, in which case advacne one mile and take 1 day

        # decide if fording will succeed or fail
        ford_failure = True if uniform() < self.current_stop.ford_failure_rate(self.date) else False
        # decide how much food is lost by fording
        lost_food = self.inventory['food'] * (1.0 if uniform() < self.current_stop.ford_food_loss_fraction(self.date) else 0.0)

        # made it across, so advance the party        
        if not ford_failure:            
            mile_marker = self.current_stop.mile_marker
            self.current_stop = self.trail.path[mile_marker + 1]           
            
            if isinstance(self.current_stop, (River, Town)):
                # arrived at next major stop
                print 'Arrived at ' + self.current_stop['name']
                self.last_major_stop = self.current_stop
                self.next_major_stop = self.trail.next_major_stop(self.current_stop.mile_marker)
        else:
            print 'You failed to ford the river!'
            
        if lost_food > 0:
            print 'Your provisions got wet and you lost '  + str(lost_food) + ' food!'

        self.inventory['food'] = max(self.inventory['food'] - lost_food, 0.0)
        self.feed()
        self.update_health()
        self.date += timedelta(days=1)

        return


    def caulk(self):
        """
        Simulate caulking to cross a river. It takes one day. Update the condition of the party.

        Returns
        -------
        """

        # caulking can fail in which case the party does not advance and loses 1 day of food
        # caulking can cause food to get wet and be considered lost
        # caulking can succeed, in which case advacne one mile and take 1 day

        # decide if caulking will succeed or fail
        caulk_failure = True if uniform() < self.current_stop.caulk_failure_rate(self.date) else False
        # decide how much food is lost by fording
        lost_food = self.inventory['food'] * (1.0 if uniform() < self.current_stop.caulk_food_loss_fraction(self.date) else 0.0)

        # made it across, so advance the party        
        if not caulk_failure:            
            mile_marker = self.current_stop.mile_marker
            self.current_stop = self.trail.path[mile_marker + 1]           
            
            if isinstance(self.current_stop, (River, Town)):
                # arrived at next major stop
                print 'Arrived at ' + self.current_stop['name']
                self.last_major_stop = self.current_stop
                self.next_major_stop = self.trail.next_major_stop(self.current_stop.mile_marker)
        else:
            print 'You failed to cross the river by caulking!'
            
        if lost_food > 0:
            print 'Your provisions got wet and you lost '  + str(lost_food) + ' food!'

        self.inventory['food'] = max(self.inventory['food'] - lost_food, 0.0)
        self.feed()
        self.update_health()
        self.date += timedelta(days=1)

        return
