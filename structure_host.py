import string

import structure_base



class Hosts(structure_base.Collection):
	""" tracks all known hosts """
	def __init__(self, app):
		# call super
		super(Hosts,self).__init__(app,"known_hosts",Host)

	def keyFromArguments(self, name):
		""" get the key from the arguments """
		return name
	def objToRawData(self, obj):
		""" converts an object into raw data """
		return {"name": obj.name}
	def rawDataToArgDict(self, raw):
		""" brings obj into a form which can be consumed by cls """
		return {"name": raw["name"]}
	
	def fuzzyMatch(self, hostname):
		""" matches the host name in a fuzzy way against the known hosts """
		
		hostname = hostname.strip()
		fuzzy_match = []
		
		# try to match host to a known host
		for known_host in self.getAll():
			# in case of an exact match, add the token and end the loop
			if known_host.name == hostname:
				#print(host,"->",known_host)
				return known_host
			# in case of a fuzzy match, add the host to the fuzzy match list
			fuzzy = lambda s: s.lower().replace(' ','')
			if fuzzy(known_host.name) == fuzzy(hostname):
				#print(host,"~>",known_host)
				fuzzy_match.append(known_host)
		else:
			# if there was no exact match, see if we have at least fuzzy matches
			if len(fuzzy_match) == 0:
				raise ValueError("Could not parse the host name '%s': no candidates." % hostname)
			elif len(fuzzy_match) >= 2:
				raise ValueError("Could not parse the host name '%s': too many candidates: %s" % (hostname,fuzzy_match))
			else:
				# if there is only one fuzzy match, use it
				return fuzzy_match[0]


class Host:
	""" encodes information of one host """
	
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
		""" return the repositories on the current machine """
		return {repo for repo in self.app.repositories.getAll() if repo.host == self}
	
	def connections(self):
		""" return the connections from the current machine """
		return {conn for conn in self.app.connections.getAll() if conn.source == self}
	
	#
	# hashable type mehods, hashable is needed for dict keys and sets
	# (source: http://docs.python.org/2/library/stdtypes.html#mapping-types-dict)
	#
	def __hash__(self):
		return hash(self.name)
	
	def __eq__(self, other):
		return self.name == other.name

	def __repr__(self):
		return "Host(%r)" % self.name

	def __str__(self):
		return "Host(%s)" % self.name
 
 
  
