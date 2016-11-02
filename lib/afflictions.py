class Affliction():
    """
    Defines a member of the travelling party.
    """
    def __init__(self, affliciton_def=None):
        assert affliciton_def is not None, 'ERROR - you need to provide an affliction definition dictionary.'

        try:
            self.name = affliciton_def['name']
            self.severity = affliciton_def['severity']
        except:
            print 'There was an error reading the affliction definition dictionary:'
            print affliciton_def
            raise
