class FuzzyMatch:
    def __init__(self, s, valid):
        # save options
        self.s = s = s.strip()
        self.valid = valid

        # initialise output variables
        self.match = None
        self.fuzzyMatches = {}

        # process data
        self._match()

    def _match(self):
        """
            matches the s in a fuzzy way against the keys of the dictionary valid,
            if there is an exact match, the value is saved in self.match
            if there is no exact match, all fuzzy matches are saved in self.fuzzyMatches
        """
        # try to match s to a valid key
        for key, value in self.valid.items():
            # in case of an exact match, use the token
            if self.s == key:
                self.match = value
                return

            # in case of a fuzzy match, add the item to the fuzzy match dictionary
            fuzzy = lambda s: s.lower().replace(' ', '')
            if fuzzy(key).startswith(fuzzy(self.s)):
                self.fuzzyMatches[key] = value

    def one(self):
        """ get one result, if there are more or less possibilities, raise an error """
        if self.match is not None:
            # if an exact match was found, use it
            return self.match
        else:
            # if there was no exact match, see if we have at least fuzzy matches
            if len(self.fuzzyMatches) == 1:
                # if there is only one fuzzy match, return the corresponding value
                return list(self.fuzzyMatches.values()).pop()
            elif len(self.fuzzyMatches) == 0:
                # otherwise raise the corresponding error
                candidates = ", ".join(sorted(key for key in self.valid.keys()))
                raise ValueError("no candidates, valid candidates: %s" % candidates)
            else:
                candidates = ", ".join(sorted(key for key in self.fuzzyMatches.keys()))
                raise ValueError("too many candidates: %s" % candidates)

    def all(self):
        """ get all found results """
        if self.match is not None:
            # if an exact match was found, use it
            return [self.match]
        else:
            # otherwise use the fuzzy matches
            return self.fuzzyMatches.values()


def fuzzyMultiMatch(s, valid):
    """
        matches the s in a fuzzy way against the keys of the dictionary valid,
        the corresponding values are returned
    """
    return FuzzyMatch(s, valid).all()


def fuzzyMatch(s, valid):
    """
        matches the s in a fuzzy way against the keys of the dictionary valid,
        the corresponding value is returned
    """
    return FuzzyMatch(s, valid).one()
