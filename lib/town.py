from stop import Stop

class Town(Stop):
    '''
    Town is a special stop along the trail offering rest, repairs, and trade
    '''

    def __init__(self, name='town', mile_marker=None, add_actions=None, rem_actions=None, properties=None):
        Stop.__init__(self)

        self.kind = 'town'

        if name == 'town':
            self.name = 'town ' + str(mile_marker)
        else:
            self.name = name

        self.mile_marker = mile_marker

        # default actions
        # if nothing passed, use these defaults
        if add_actions is None:
            add_actions = list()

        if rem_actions is None:
            rem_actions = list()

        if properties is None:
            properties = dict()

        self.actions.update(set(add_actions))
        self.actions.difference_update(set(rem_actions))

        self.properties.update(properties)

