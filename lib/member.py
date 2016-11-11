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
            self.base_speed = member_def['abilities']['speed']
            self.inventory = member_def['inventory']
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

    def update_health(self, elapsed_time):
        if self.health > 0:
            for affliction in self.afflictions.values():
                self.health -= affliction.severity * elapsed_time
                if self.health <= 0:
                    print self.name + ' has died of ' + affliction.name
                    self.food_need = None
                    self.water_need = None

    # as time passes, you become hungier, thirstier, and more tiered
    # when you eat, drink, or rest you reduce these

    def update_hunger(self, elapsed_time):
        self.afflictions['hunger'].severity += elapsed_time


    def update_thirst(self, elapsed_time):
        self.afflictions['thirst'].severity += elapsed_time


    def update_fatigue(self, elapsed_time):
        self.afflictions['fatigue'].severity += elapsed_time


    def update_weariness(self, elapsed_time):
        self.update_hunger(elapsed_time)
        self.update_thirst(elapsed_time)
        self.update_fatigue(elapsed_time)


    def pack_weight(self):
        pack_weight = 0
        for item in ['food', 'water', 'gear']:
            pack_weight += self.inventory.get(item)

        return pack_weight


    def weight_speed_modifier(self):
        pw = self.pack_weight()
        # 0 for empty pack, 1 for heavy pack - steep ramp from 0 to 1 at 50 pounds+
        return (tanh(-0.5*(pw - 50)) + 1.0)*0.5


    def weighted_speed(self):
        return self.weight_speed_modifier() * self.base_speed