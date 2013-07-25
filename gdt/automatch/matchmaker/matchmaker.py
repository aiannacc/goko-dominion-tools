
# A matchmaker generates Match objects from Seek objects. This is an abstract
# class.
class Matchmaker():

    # Returns Match objects generated from the given Seek objects
    def generate_matches(self, seeks):
        return NotImplemented
