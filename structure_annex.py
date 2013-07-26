import string

import structure_base


class Annexes(structure_base.Collection):
	""" tracks all known annexes """
	def __init__(self, app):
		# call super
		super(Annexes,self).__init__(app,"known_annexes",Annex)

	def keyFromArguments(self, name):
		""" get the key from the arguments """
		return name
	def objToRawData(self, obj):
		""" converts an object into raw data """
		return {"name": obj.name}
	def rawDataToArgDict(self, raw):
		""" brings obj into a form which can be consumed by cls """
		return {"name": raw["name"]}

	def fuzzyMatch(self, annexname):
		""" matches the annex name in a fuzzy way against the known annexes """
		
		annexname = annexname.strip()
		fuzzy_match = []
		
		# try to match annex to a known annex
		for known_annex in self.getAll():
			# in case of an exact match, add the token and end the loop
			if known_annex.name == annexname:
				#print(annex,"->",known_annex)
				return known_annex
			# in case of a fuzzy match, add the annex to the fuzzy match list
			fuzzy = lambda s: s.casefold().replace(' ','')
			if fuzzy(known_annex.name).startswith( fuzzy(annexname) ):
				#print(annex,"~>",known_annex)
				fuzzy_match.append(known_annex)
		else:
			# if there was no exact match, see if we have at least fuzzy matches
			if len(fuzzy_match) == 0:
				raise ValueError("Could not parse the annex name '%s': no candidates." % annexname)
			elif len(fuzzy_match) >= 2:
				candidates = ", ".join(sorted(annex.name for annex in fuzzy_match))
				raise ValueError("Could not parse the annex name '%s': too many candidates: %s" % (annexname,candidates))
			else:
				# if there is only one fuzzy match, use it
				return fuzzy_match[0]
	
class Annex:
	""" encodes information of one annex """
	
	VALID_CHARS = (set(string.ascii_letters + string.digits + string.punctuation) | {' '}) - {'"',"'"}
	
	def __init__(self, app, name):
		# save options
		self.app = app
		self._name = name

		assert self.name, "name may not be empty"
		assert set(self.name).issubset(self.VALID_CHARS), "%s: invalid character detected." % self
		assert not self.name.startswith(" ") or not self.name.endswith(" "), "%s: name may not start nor end with a white space." % self
	
	@property
	def name(self):
		return self._name
	
	def repositories(self):
		""" return the repositories belonging to the current annex """
		return {repo for repo in self.app.repositories.getAll() if repo.annex == self}

	#
	# hashable type mehods, hashable is needed for dict keys and sets
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

