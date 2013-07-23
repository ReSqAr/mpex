import collections
import os
import subprocess

import structure_base
import structure_host
import structure_annex


class Repositories(structure_base.Collection):
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
		assert isinstance(self._host,structure_host.Host), "%s: host has to be an instance of Host" % self
		assert isinstance(self._annex,structure_annex.Annex), "%s: annex has to be an instance of Annex" % self
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
				raise ValueError("too many ')' in: %s" % files)
		else:
			if number_of_brackets > 0:
				raise ValueError("too many '(' in: %s" % files)
		
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
	def localpath(self):
		""" returns the path on the local machine """
		# TODO: fix for non-local repositories
		return self.path
	
	@property
	def direct(self):
		""" determines if the repository should be in direct mode, default: False """
		return self._data.get("direct","false").lower() == "true"
	@direct.setter
	def direct(self,v):
		self._data["direct"] = str(bool(v)).lower()
	
	@property
	def trust(self):
		""" gives the trust level of the repository, default: semitrust """
		return self._data.get("trust","semitrust")
	@trust.setter
	def trust(self,v):
		assert v in ("semitrust","trust","untrust"), "Trust has to be valid, is '%s'." % v
		self._data["trust"] = v

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
	
	def connectedRepositories(self):
		""" find all connected repositories, returns a dictionary: repository -> set of connections """
		
		# convert connections to a dictionary dest -> set of connections to dest
		connections = collections.defaultdict(set)
		for connection in self.host.connections():
			connections[connection.dest].add(connection)
		
		# get repositories
		repositories = self.annex.repositories()
		
		# return the desired dictionary
		return {r:connections[r.host] for r in repositories if r.host in connections}

	
	#
	# file system methods
	#
	def init(self):
		""" inits the repository """
		# get path
		path = os.path.normpath(self.localpath)
		# create the path if needed
		if not os.path.isdir(path):
			os.makedirs(path)
		# change to it
		os.chdir(path)
		# make really sure that we are, where we want to be
		assert os.path.normpath(os.getcwd()) == path, "We are in the wrong directory?!?"

		print("\033[1;37;44m initialise %s in %s \033[0m" % (self.annex.name,path))

		# init git
		if not os.path.isdir(os.path.join(path,".git")):
			subprocess.check_call(["git","init"])
		else:
			print("It is already a git repository.")
		
		# init git annex
		if not os.path.isdir(os.path.join(path,".git/annex")):
			subprocess.check_call(["git-annex","init",self.annex.name])
		else:
			print("It is already a git annex repository.")
		
		# set the properties
		self.setProperties()
	
	def setProperties(self):
		""" sets the properties  the current repository """
		# get path
		path = os.path.normpath(self.localpath)
		assert os.path.isdir(os.path.join(path,".git/annex")), "This is not a git annex repository."
		# change to it
		os.chdir(path)
		# make really sure that we are, where we want to be
		assert os.path.normpath(os.getcwd()) == path, "We are in the wrong directory?!?"

		print("\033[1;37;44m setting properties of %s in %s \033[0m" % (self.annex.name,path))
		
		# set the requested direct mode, if doable
		if self.app.gitAnnexCapabilities["direct"]:
			d = "direct" if self.direct else "indirect"
			subprocess.check_call(["git-annex",d])
		else:
			if self.direct:
				print("direct mode requested but not supported by your git-annex version.")
		
		# set trust level
		subprocess.check_call(["git-annex",self.trust,"here"])


	#
	# hashable type mehods, hashable is needed for dict keys and sets
	# (source: http://docs.python.org/2/library/stdtypes.html#mapping-types-dict)
	#
	def __hash__(self):
		return hash((self.host,self.path))
	
	def __eq__(self, other):
		return (self.host,self.path) == (other.host,other.path)

	def __repr__(self):
		return "Repository(%r,%r,%r,%r)" % (self._host,self._annex,self._path,self._data)

	def __str__(self):
		return "Repository(%s@%s:%s:%s)" % (self._annex,self._host,self._path,self._data)


