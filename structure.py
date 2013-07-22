import json
import os
import os.path
import io
import string



class Collection:
	def __init__(self, app, filename, cls):
		# save options
		self.app = app
		self.cls = cls
		# compute the file name
		self._path = os.path.join(self.app.path,filename)
		# internal dictionary which tracks all known objects
		self._objects = {}
		# load objects
		self.load()
	
	def load(self):
		""" loads all known objects """
		# clear tracker
		self._objects.clear()
		if os.path.isfile(self._path):
			# open the file if it exists
			with io.open(self._path, mode="rt", encoding="UTF8") as fd:
				# decode list of hosts (json file)
				list_of_objects = json.load(fd)
				# create individual hosts
				for obj in list_of_objects:
					# covert raw object data
					obj = self.rawDataToArgDict(obj)
					# create the object
					self.create(**obj)
	
	def save(self):
		""" saves all known hosts """
		# get set of all known objects
		list_of_objects = list(self._objects.items())
		# convert it to a sorted list of raw data elements
		list_of_objects.sort(key=lambda kv:kv[0])
		list_of_objects = [self.objToRawData(kv[1]) for kv in list_of_objects]

		# open the file in write mode
		with io.open(self._path, mode="wt", encoding="UTF8") as fd:
			# dump data
			json.dump(list_of_objects, fd, ensure_ascii=False, indent=4, sort_keys=True)
	
	def getAll(self):
		""" return all known objects """
		return set(self._objects.values())

	def get(self, *args, **kwargs):
		"""
			get the given object, signature matches the signature of cls, however
			not all data has to specified, only the arguments are needed which are
			required to the deduce the key. if the object does not exists, None is
			returned
		"""
		# compute key
		key = self.keyFromArguments(*args, **kwargs)
		# return object
		return self._objects.get(key)

	def create(self, *args, **kwargs):
		""" get the given object, signature matches the signature of cls """
		# compute key
		key = self.keyFromArguments(*args, **kwargs)
		# if an object with the given key does not yet exists, create it
		if key not in self._objects:
			self._objects[key] = self.cls(self.app,*args,**kwargs)
		# return object
		return self._objects[key]
		
	# virtual methods
	def keyFromArguments(self, *args, **kwargs):
		""" get the key from the arguments """
		raise NotImplementedError
	def objToRawData(self, obj):
		""" converts an object into raw data """
		raise NotImplementedError
	def rawDataToArgDict(self, raw):
		""" brings obj into a form which can be consumed by cls """
		raise NotImplementedError
	
class Hosts(Collection):
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
		
class Host:
	""" encodes information of one host """
	
	VALID_CHARS = (set(string.ascii_letters + string.digits + string.punctuation) | {' '}) - {'"',"'"}
	
	def __init__(self, app, name):
		# save options
		self.app = app
		self._name = name
		
		assert set(self.name).issubset(self.VALID_CHARS), "%s: invalid character detected." % self
		assert not self.name.startswith(" ") or not self.name.endswith(" "), "%s: name may not start nor end with a white space." % self
	
	@property
	def name(self):
		return self._name
	
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
 
 
 

class Annexes(Collection):
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

	


class Annex:
	""" encodes information of one annex """
	
	VALID_CHARS = (set(string.ascii_letters + string.digits + string.punctuation) | {' '}) - {'"',"'"}
	
	def __init__(self, app, name):
		# save options
		self.app = app
		self._name = name

		assert set(self.name).issubset(self.VALID_CHARS), "%s: invalid character detected." % self
		assert not self.name.startswith(" ") or not self.name.endswith(" "), "%s: name may not start nor end with a white space." % self
	
	@property
	def name(self):
		return self._name
	
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
 

class Repositories(Collection):
	""" tracks all known repositories """
	def __init__(self, app):
		# call super
		super(Repositories,self).__init__(app,"known_repositories",Repository)

	def keyFromArguments(self, host, annex, path, **data):
		""" get the key from the arguments """
		return (host,path)
	def objToRawData(self, obj):
		""" converts an object into raw data """
		raw = dict(obj._data)
		raw["host"] = obj._host.name
		raw["annex"] = obj._annex.name
		raw["path"] = obj._path
		return raw
	def rawDataToArgDict(self, raw):
		""" brings obj into a form which can be consumed by cls """
		# copy dictionary
		raw = dict(raw)
		# convert host and annex
		raw["host"]  = self.app.hosts.create(raw["host"])
		raw["annex"] = self.app.annexes.create(raw["annex"])
		# build dictionary
		return raw

class Repository:
	""" one repository """
	
	OPERATORS = ["(",")","+","-","^","&"]
	
	def __init__(self, app, host, annex, path, **data):
		# save options
		self.app = app
		self._host = host
		self._annex = annex
		self._path = path
		self._data = data
		
		# sanity check: check that we got correct classes and path is absolute
		assert isinstance(self._host,Host), "%s: host has to be an instance of Host" % self
		assert isinstance(self._annex,Annex), "%s: annex has to be an instance of Annex" % self
		assert self._path.startswith("/"), "%s: path has to an absolute path" % self
		assert self.trust in ("semitrust","trust","untrust"), "%s: trust has to be valid." % self
		
		# sanitise the files expression
		self.files = self.files
	
	def tokeniseFileExpression(self, s):
		""" tokenises the file expression, returns a list of tokens """
		# for debugging purposes, keep the original string
		orig = s
		
		# list of tokens
		tokens = []
		# get list of known hosts
		known_hosts = self.app.hosts.getAll()
		
		while s:
			# if the first character is a white space, ignore it
			if s[0].isspace():
				s = s[1:]
				continue
			
			# if the first character is a operator, add it to the tokens list
			if s[0] in self.OPERATORS:
				tokens.append(s[0])
				s = s[1:]
				continue
			
			# hence, we have a host name
			if s[0] in {"'",'"'}:
				# the host name is enclosed in "" -> look for the next occurence
				i = s.find(s[0],1)
				if i == -1:
					# if an error occured, fail loud
					raise ValueError("Failed to parse '%s': non-closed %s found." % (orig,s[0]))
				# otherwise we found the host name
				host = s[1:i]
				s = s[i+1:]
			else:
				# find the next operator (or the end of the string)
				indices = [s.find(op) for op in self.OPERATORS]
				indices = [index for index in indices if index >= 0]
				
				if indices:
					# if there is a next operator, use it
					i = min(indices)
				else:
					# otherwise, use the end of the string
					i = len(s)
				
				# extract host name and set new s
				host = s[:i]
				s = s[i:]
			
			# we have found a host name, now parse it
			host = host.strip()
			
			fuzzy_match = []
			# try to match host to a known host
			for known_host in known_hosts:
				# in case of an exact match, add the token and end the loop
				if known_host.name == host:
					#print(host,"->",known_host)
					tokens.append(known_host.name)
					break
				# in case of a fuzzy match, add the host to the fuzzy match list
				fuzzy = lambda s: s.lower().replace(' ','')
				if fuzzy(known_host.name) == fuzzy(host):
					#print(host,"~>",known_host)
					fuzzy_match.append(known_host)
			else:
				# if there was no exact match, see if we have at least fuzzy matches
				if len(fuzzy_match) == 0:
					raise ValueError("Could not parse the host name '%s': no candidates." % host)
				elif len(fuzzy_match) >= 2:
					raise ValueError("Could not parse the host name '%s': too many candidates." % host)
				else:
					# if there is only one fuzzy match, use it
					tokens.append(fuzzy_match[0].name)
		
		# return the list of tokens
		return tokens
		
	def sanitiseFilesExpression(self, files):
		""" sanitise the files expression """
		
		# if there is nothing to do, leave
		if files is None:
			return
		
		# tokenise
		tokens = self.tokeniseFileExpression(files)
		
		# some trivial properties which have to fullfilled:
		# brackets: all brackets have to closed at the right level
		number_of_brackets = 0
		for token in tokens:
			if token == "(": number_of_brackets += 1
			if token == ")": number_of_brackets -= 1
			if number_of_brackets < 0:
				raise ValueError("Too many ')' in: %s" % files)
		else:
			if number_of_brackets > 0:
				raise ValueError("Too many '(' in: %s" % files)
		
		# reformat files
		files = ""
		for token in tokens:
			# if the host contains a white space, add around it ''
			if ' ' in token:
				token = "'%s'" % token
			# kill the last white space in case of )
			if token == ')' and files[-1] == " ":
				files = files[:-1]
			# add token
			files += token
			# white space after token, unless it is (
			if token != '(':
				files += " "
		
		return files.strip()
		
	@property
	def host(self):
		return self._host
	
	@property
	def annex(self):
		return self._annex
	
	@property
	def path(self):
		return self._path
	
	@property
	def direct(self):
		""" determines if the repository should be in direct mode, default: False """
		return self._data.get("direct","false").lower() == "true"
	
	@property
	def files(self):
		""" determines which files should be kept in the repository, default: None """
		return self._data.get("files")
	
	@files.setter
	def files(self,v):
		""" protected setter method """
		# sanitise the expression
		v = self.sanitiseFilesExpression(v)
		
		if v is None and "files" in self._data:
			# if it should be deleted and the property is set
			del self._data["files"]
		elif v is not None:
			# if the property should be set
			self._data["files"] = v
	
	@property
	def strict(self):
		""" determines if ONLY files which match the files epxression should be kept, default: False """
		return self._data.get("strict","false").lower() == "true"
	
	@strict.setter
	def strict(self,v):
		self._data["strict"] = str(bool(v)).lower()

	@property
	def trust(self):
		""" gives the trust level of the repository, default: semitrust """
		return self._data.get("trust","semitrust")


	def __repr__(self):
		return "Repository(%r,%r,%r,%r)" % (self._host,self._annex,self._path,self._data)

	def __str__(self):
		return "Repository(%s@%s:%s:%s)" % (self._annex.name,self._host.name,self._path,self._data)


class Connections(Collection):
	""" tracks all known connections """
	def __init__(self, app):
		# call super
		super(Connections,self).__init__(app,"known_connections",Connection)

	def keyFromArguments(self, source, dest, path, **data):
		""" get the key from the arguments """
		return (source,dest,path)
	def objToRawData(self, obj):
		""" converts an object into raw data """
		raw = dict(obj._data)
		raw["source"] = obj._source.name
		raw["dest"] = obj._dest.name
		raw["path"] = obj._path
		return raw
	def rawDataToArgDict(self, raw):
		""" brings obj into a form which can be consumed by cls """
		# copy dictionary
		raw = dict(raw)
		# convert source and dest
		raw["source"] = self.app.hosts.create(raw["source"])
		raw["dest"]   = self.app.hosts.create(raw["dest"])
		# build dictionary
		return raw

class Connection:
	""" encodes information of one connection """
	def __init__(self, app, source, dest, path, **data):
		# save options
		self.app = app
		self._source = source
		self._dest = dest
		self._path = path
		self._data = data
		
		# sanity check: check that we got correct classes and path is valid,
		# path maybe: ssh://<host> or <absolute path>
		assert isinstance(self._source,Host), "%s: source has to be an instance of Host" % self
		assert isinstance(self._dest,Host), "%s: dest has to be an instance of Host" % self
		assert self._path.startswith("ssh://") or self._path.startswith("/"), "%s: unknown protocol specified in path" % self

	@property
	def source(self):
		return self._source
	
	@property
	def dest(self):
		return self._dest
	
	@property
	def path(self):
		return self._path
	
	@property
	def alwaysOn(self):
		""" specifies if the connection is always active, default: False """
		return self._data.get("alwayson","false").lower() == "true"
	@alwaysOn.setter
	def alwaysOn(self,v):
		self._data["alwayson"] = str(bool(v)).lower()


	def __repr__(self):
		return "Connection(%r,%r,%r,%r)" % (self._source,self._dest,self._path,self._data)

	def __str__(self):
		return "Connection(%s->%s:%s:%s)" % (self._source.name,self._dest.name,self._path,self._data)

 