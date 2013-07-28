import collections
import string

import lib.fuzzy_match

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

	def check(self):
		""" checks the files expressions """
		for repo in self.getAll():
			repo.files = repo.files

	def fuzzyMatch(self, annex, annex_desc):
		""" matches the annex description in a fuzzy way against the known repositories """
		
		# create key -> value mapping
		valid = {repo.description : repo for repo in self.getAll() if repo.annex == annex}
		
		try:
			# try to find a 
			return lib.fuzzy_match.fuzzyMatch(annex_desc, valid)
		except ValueError as e:
			raise ValueError("could not parse the annex description '%s': %s" % (annex_desc,e.args[0]))

class Repository:
	"""
		one repository
		
		syntax of a 'files expression':
			operators:
				(,)   brackets
				+     or operator
				-     not operator
				&     and operator (standard)
			other tokens: descriptions of repositories (usually host names)
			
	"""
	
	OPERATORS = ("(",")","+","-","&")
	TRUST_LEVEL = ("semitrust","trust","untrust")
	VALID_DESC_CHARS = set(string.ascii_letters + string.digits + "_")
	
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
		assert self.trust in self.TRUST_LEVEL, "%s: trust has to be valid." % self
		assert self.description, "%s: the git annex description has to be non-empty"
		assert set(self.description).issubset(self.VALID_DESC_CHARS), "%s: invalid character detected." % self
		
		# we are unable to check files here, as for that all repositories have to exist,
		# so we check it after everything is loaded
		
	def tokeniseFileExpression(self, s):
		""" tokenises the file expression, returns a list of tokens """
		if s is None:
			return []
		
		# for debugging purposes, keep the original string
		orig = s
		
		# list of tokens
		tokens = []
		
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
			
			# hence, we have a annex description
			if s[0] in {"'",'"'}:
				# the annex description is enclosed in "" -> look for the next occurence
				i = s.find(s[0],1)
				if i == -1:
					# if an error occured, fail loud
					raise ValueError("Failed to parse '%s': non-closed %s found." % (orig,s[0]))
				# otherwise we found the annex description
				annex_desc = s[1:i]
				s = s[i+1:]
			else:
				# find the next operator (or the end of the string)
				indices = [s.find(op) for op in self.OPERATORS]
				indices = [index for index in indices if index >= 0]
				
				# if there is a next operator, use it,
				# otherwise use the end of the string
				i = min(indices) if indices else len(s)
				# extract annex description set new s
				annex_desc = s[:i]
				s = s[i:]
			
			# we have found an annex description, now parse it
			annex_desc = self.app.repositories.fuzzyMatch(self.annex,annex_desc)
			tokens.append(annex_desc.description)
		
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
			# if the annex description contains a white space, add around it ''
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
		
	def tokenisedFilesExpressionToCmd(self, tokens):
		""" converts a list of tokens into a command """
		debug = " ".join(tokens)
		tokens,cmd = list(tokens),[]
		
		# special treatment of tokens = ["-"]
		if tokens == ["-"]:
			# this means, no file should be in the repository
			return ["--exclude=*"]
		
		while tokens:
			# get first token
			token = tokens.pop(0)
			
			if not token in self.OPERATORS:
				# example: Host1, effect: selects all files on this remote
				cmd.extend(["--in=%s"%token])
			elif token == "(":
				cmd.extend(["-("])
			elif token == ")":
				cmd.extend(["-)"])
			elif token == "-":
				# example: - Host2, effect: selects the files which are not present on the remote
				cmd.extend(["--not"])
			elif token == "+":
				# example: Host1 + Host2, effect: selects files which are present on at least one remotes
				cmd.extend(["--or"])
			elif token == "&":
				# example: Host1 & Host2, effect: selects files which are present on both remotes
				cmd.extend(["--and"])
			else:
				raise ValueError("Programming error: %s" % token)
		
		return cmd
	
	def checkFilesExpression(self, files):
		"""
			checks if a files expression looks correct, if it is incorrect,
			an error is raised
		"""
		files = self.sanitiseFilesExpression(files)
		files = self.tokeniseFileExpression(files)
		self.tokenisedFilesExpressionToCmd(files)
	
	@property
	def host(self):
		return self._host
	
	@property
	def annex(self):
		return self._annex
	
	@property
	def path(self):
		return self._path
	
	def hasNonTrivialDescription(self):
		""" is the description more than the modified host name? """
		return "description" in self._data
	
	@property
	def description(self):
		""" the git annex description of the repository, default: host name """
		if "description" not in self._data:
			# filter unwanted characters
			description = "".join(c for c in self.host.name if c in self.VALID_DESC_CHARS)
			if not description:
				raise ValueError("%s: cannot generate a valid git annex description." % self)
			return description
		else:
			return self._data["description"]
	
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
		assert v in self.TRUST_LEVEL, "Trust has to be valid, is '%s'." % v
		self._data["trust"] = v

	@property
	def files(self):
		""" determines which files should be kept in the repository, default: None """
		files = self._data.get("files")
		files = self.sanitiseFilesExpression(files)
		return files
	
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
		""" determines if ONLY files which match the files expression should be kept, default: False """
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


