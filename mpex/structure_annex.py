import string

from .lib import fuzzy_match

from . import structure_base


class Annexes(structure_base.Collection):
    """ tracks all known annexes """

    def __init__(self, app):
        # call super
        super(Annexes, self).__init__(app, "known_annexes", Annex)

    def key_from_arguments(self, name):
        """ get the key from the arguments """
        return name

    def obj_to_raw_data(self, obj):
        """ converts an object into raw data """
        return {"name": obj.name}

    def raw_data_to_arg_dict(self, raw):
        """ brings obj into a form which can be consumed by cls """
        return {"name": raw["name"]}

    def fuzzy_match(self, annex_name):
        """ matches the annex name in a fuzzy way against the known annexes """

        # create key -> value mapping
        valid = {annex.name: annex for annex in self.get_all()}

        try:
            # try to find an annex
            return fuzzy_match.fuzzy_match(annex_name, valid)
        except ValueError as e:
            raise ValueError("could not parse the annex name '%s': %s" % (annex_name, e.args[0]))


class Annex:
    """ encodes information of one annex """

    VALID_CHARS = (set(string.ascii_letters + string.digits + string.punctuation) | {' '}) - {'"', "'"}

    def __init__(self, app, name):
        # save options
        self.app = app
        self._name = name

        assert self.name, \
            "name may not be empty"
        assert set(self.name).issubset(self.VALID_CHARS), \
            "%s: invalid character detected." % self
        assert not self.name.startswith(" ") or not self.name.endswith(" "), \
            "%s: name may not start nor end with a white space." % self

    @property
    def name(self):
        return self._name

    def repositories(self):
        """ return the repositories belonging to the current annex """
        return {repo for repo in self.app.repositories.get_all() if repo.annex == self}

    #
    # hashable type methods, hashable is needed for dict keys and sets
    # (source: http://docs.python.org/2/library/stdtypes.html#mapping-types-dict)
    #
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return "Annex(%r)" % self.name

    def __str__(self):
        return "Annex(%s)" % self.name
