
# A matchmaker generates Match objects from Seek objects. This is an abstract
# class.
class Matchmaker():

    def get_description(self):
        return NotImplemented

    def generate_matches(self, seeks):
        return NotImplemented
