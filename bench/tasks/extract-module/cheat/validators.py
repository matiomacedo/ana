class Validator:
    def __init__(self, minimum):
        self.minimum = minimum

    def check(self, value):
        return value >= self.minimum
