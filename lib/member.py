from afflictions import Affliction

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
            self.speed = member_def['abilities']['speed']
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
