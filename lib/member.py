from afflictions import Affliction
from numpy import tanh

class Member():
    """
    Defines a member of the travelling party.
    """
    def __init__(self, member_def=None):
        assert member_def is not None, 'ERROR - you need to provide a member definition dictionary.'

        try:
            self.name = member_def['name']
            self.health = member_def['condition']['health']
            self.food_need = member_def['needs']['food']
            self.water_need = member_def['needs']['water']
            self.base_speed = float(member_def['abilities']['speed'])
            self.inventory = member_def['inventory']
            self.body_weight = float(member_def['condition']['weight'])
        except:
            print 'There was an error reading the member definition dictionary:'
            print member_def
            raise

        hunger = Affliction({'name': 'hunger', 'severity': 0})
        thirst = Affliction({'name': 'thirst', 'severity': 0})
        fatigue = Affliction({'name': 'fatigue', 'severity': 0})

        self.afflictions = dict([(a.name, a) for a in [hunger, thirst, fatigue]])

        for affliction_def in member_def.get('afflictions', list()):
            a = Affliction(affliction_def)
            self.afflictions[a.name] = a

    def print_status(self):
        print 'Health:', self.health
        print '(Hunger, Thirst, Fatigue):', [self.afflictions[a].severity for a in ['hunger', 'thirst', 'fatigue']]
        print '(Food, Water, Weight):', [self.inventory.get('food'), self.inventory.get('water'), self.pack_weight()]


    def update_health(self, elapsed_time, danger=None, danger_severity=None):
        # a danger is a one-time event that causes harm, like a bear attack
        if danger is not None and self.health > 0:
            self.health -= danger_severity
            if self.health <= 0:
                print self.name + ' has died of ' + danger
                self.food_need = None
                self.water_need = None

        # an affliction is a long-term condition that causes harm
        for affliction in self.afflictions.values():
            if self.health > 0:
                self.health -= affliction.severity * elapsed_time
                if self.health <= 0:
                    print self.name + ' has died of ' + affliction.name
                    self.food_need = None
                    self.water_need = None

    # as time passes, you become hungrier, thirstier, and more tiered
    # when you eat, drink, or rest you reduce these

    def update_hunger(self, elapsed_time):
        # a = 200 / (lifetime * 24) ^ 2
        # lifetime = 7 --> a = 0.007
        self.afflictions['hunger'].severity += 0.007 * elapsed_time


    def update_thirst(self, elapsed_time):
        # a = 200 / (lifetime * 24) ^ 2
        # lifetime = 3 --> a = 0.039
        self.afflictions['thirst'].severity += 0.039 * elapsed_time


    def update_fatigue(self, elapsed_time):
        # a = 200 / (lifetime * 24) ^ 2
        # lifetime = 3 --> a = 0.039
        self.afflictions['fatigue'].severity += 0.039 * elapsed_time


    def update_weariness(self, elapsed_time):
        self.update_hunger(elapsed_time)
        self.update_thirst(elapsed_time)
        self.update_fatigue(elapsed_time)


    def pack_weight(self):
        pack_weight = 0
        for item in ['food', 'water', 'gear']:
            pack_weight += self.inventory.get(item)

        return float(pack_weight)


    def weight_speed_modifier(self):
        pw = self.pack_weight()
        # 0 for empty pack, 1 for heavy pack - steep ramp from 0 to 1 at 50 pounds+
        return 1.0 / (((3600/mph) + (pw/bw*100*6))/3600.0)


    def weighted_speed(self):
        # based on rule: 6 additional seconds per mile for every 1% of body weight in pack
        return 1.0 / (((3600/self.base_speed) + (self.pack_weight()/self.body_weight*100*6))/3600.0)