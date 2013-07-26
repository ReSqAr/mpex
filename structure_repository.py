import collections
import os
import subprocess
import datetime
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
		
		
		main methods:
			init()
			setProperties()
			finalise()
			sync(annex descriptions)
			repairMaster()
			copy(annex descriptions, files expression, strict=True/false)
			
		other methods:
			changePath()

			readGitKey(key) -> reads key
			gitBranches() -> list of branches
			hasUncommitedChanges() -> True/False

			getGitAnnexStatus() -> dictionary
			getAnnexUUID() -> uuid
			onDiskDirectMode() -> "direct"/"indirect"
			onDiskTrustLevel() -> element of TRUST_LEVEL
			
			activeAnnexDescriptions() -> dictionary online repositories -> connection
		
		syntax of a 'files expression':
			TODO
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
	
	@property
	def localpath(self):
		""" returns the path on the local machine """
		if self.app.currentHost() != self.host:
			raise ValueError("The current host is not the host of the repository. (%s != %s)" % (self.app.currentHost(),self.host))
		return self.path
	
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
	# file system interaction
	#
	def execute_command(self, cmd, ignoreexception=False):
		""" print and execute the command """
		print("command:"," ".join(cmd))
		try:
			subprocess.check_call(cmd)
		except subprocess.CalledProcessError:
			if ignoreexception:
				pass
			else:
				raise


	def changePath(self, create=False):
		""" change the path to the current repository """

		# get path
		path = os.path.normpath(self.localpath)
		
		if create:
			# create the path if needed
			if not os.path.isdir(path):
				os.makedirs(path)
		else:
			# if we are not allowed to create it, it has to be git annex archive
			assert os.path.isdir(os.path.join(path,".git/annex")), "%s is not a git annex repository, please run 'init' first." % path
			
		# change to it
		os.chdir(path)
		
		# make really sure that we are, where we want to be
		assert os.path.normpath(os.getcwd()) == path, "We are in the wrong directory?!?"
		
		return path
	
	
	def readGitKey(self, key):
		""" read a git key """
		# change path
		self.changePath()
		
		# get output of 'git config $key'
		output = subprocess.check_output(["git","config",key]).decode("UTF-8").strip()
		assert output, "Error."
		
		# and return it
		return output
	
	def gitBranches(self):
		""" returns all known branches """
		# change path
		self.changePath()

		# call 'git branch'
		output = subprocess.check_output(["git","branch"]).decode("UTF8")
		# the first two characters are noise
		return [line[2:].strip() for line in output.splitlines() if line.strip()]

	def hasUncommitedChanges(self):
		""" has the current repository uncommited changes? """

		# change into the right directory
		path = self.changePath()

		return bool(subprocess.check_output(["git","status","-s"]).decode("UTF8").strip())
	
	
	
	def getGitAnnexStatus(self):
		""" calls 'git-annex status --fast' and parses the output """
		# change path
		self.changePath()

		# call the command
		cmd = ["git-annex","status","--fast"]
		with open(os.devnull, "w") as devnull:
			output = subprocess.check_output(cmd,stderr=devnull).decode("UTF-8")
		
		# parse it
		status,lastkey = {},None
		for line in output.splitlines():
			# ignore empty lines
			if not line.strip():
				continue
			
			# if the line does not start with a space, we have line of type 'key: value'
			if not line[0].isspace():
				# split it
				key, value = line.split(':',1)
				# remove white spaces
				key, value = key.strip(), value.strip()
				# recored it
				status[key] = value
				lastkey = key
			else:
				# if we have a line which starts with a white space,
				# then add it to '$lastkey - list'
				assert lastkey is not None, "invalid output"
				key = "%s - list" % lastkey
				
				# create the list if necessary
				if key not in status:
					status[key] = []
				
				# append the current line
				status[key].append(line.strip())
		
		return status
		
	def getAnnexUUID(self):
		""" get the git annex uuid of the current repository """
		return self.readGitKey("annex.uuid")
	
	def onDiskDirectMode(self):
		""" finds the on disk direct mode """
		
		# if the current version does not have direct mode capability, return indirect
		if not self.app.gitAnnexCapabilities["direct"]:
			return "indirect"
		
		# get git annex status
		status = self.getGitAnnexStatus()
		
		# read the mode
		assert "repository mode" in status, "Invalid git-annex output"
		mode = status["repository mode"]
		assert mode in ("direct","indirect"), "Unknown direct mode detected: %s" % mode
		return mode

	def onDiskTrustLevel(self):
		""" determines the current trust level """

		# get git annex status and git annex uuid
		uuid = self.getAnnexUUID()
		status = self.getGitAnnexStatus()
		
		for level in self.TRUST_LEVEL:
			# create key
			key = "%sed repositories - list" % level
			
			# if there is repository on the current trust level, ignore it
			if key not in status:
				continue
			
			# read the list of repositories, format: UUID -- name
			repos = status[key]
			
			for repo in repos:
				# find the repository with our current uuid
				if repo.startswith(uuid):
					return level
		else:
			raise ValueError("Unable to determine the trust level.")



	def activeRepositories(self):
		""" determine repositories which are online """
		active_repos = collections.defaultdict(set)
		
		for repository, connections in self.connectedRepositories().items():
			for connection in connections:
				if connection.isOnline():
					# add the connection
					active_repos[repository].add(connection)
		
		return active_repos





	def init(self, ignorenonempty=False):
		""" inits the repository """
		
		# change into the right directory, create it if necessary
		path = self.changePath(create=True)

		print("\033[1;37;44m initialise %s at %s \033[0m" % (self.annex.name,path))

		# init git
		if not os.path.isdir(os.path.join(path,".git")):
			if os.listdir(path) and not ignorenonempty:
				raise RuntimeError("Trying to run 'git init' in a non-empty directory, set ignorenonempty=True.")
			else:
				self.execute_command(["git","init"])
		else:
			print("It is already a git repository.")
		
		# init git annex
		if not os.path.isdir(os.path.join(path,".git/annex")):
			self.execute_command(["git-annex","init",self.description])
		else:
			print("It is already a git annex repository.")
		
		# set the properties
		self.setProperties()
	
	def setProperties(self):
		""" sets the properties of the current repository """
		
		# change into the right directory
		path = self.changePath()

		print("\033[1;37;44m setting properties of %s at %s \033[0m" % (self.annex.name,path))
		
		# set the requested direct mode, if doable
		if self.app.gitAnnexCapabilities["direct"]:
			# change only if needed
			d = "direct" if self.direct else "indirect"
			if self.onDiskDirectMode() != d:
				self.execute_command(["git-annex",d])
		else:
			if self.direct:
				print("direct mode is requested, however it is not supported by your git-annex version.")
		
		# set trust level if necessary
		if self.onDiskTrustLevel() != self.trust:
			self.execute_command(["git-annex",self.trust,"here"])
		
		# set git remotes
		for repo, connections in self.connectedRepositories().items():
			# make sure that we have only one connection
			assert connections, "Programming error."
			assert len(connections) == 1, "Git supports only up to one connection."
			
			# select connection and get details
			connection = connections.pop()
			gitID   = repo.description
			gitPath = connection.gitPath(repo)
			
			try:
				# determine which url was already set
				url = self.readGitKey("remote.%s.url" % gitID)
			except subprocess.CalledProcessError:
				# no url was yet set
				url = None
			
			if not url:
				# if no url was yet set, set it
				self.execute_command(["git","remote","add",gitID,gitPath])
			else:
				# otherwise, check that the correct one has been set
				if url != gitPath:
					raise RuntimeError("The url set for the connection %s does not match the computed one." % connection)
				else:
					continue
	
	def finalise(self):
		""" calls git-annex add and commits all changes """
		
		# change into the right directory
		path = self.changePath()

		print("\033[1;37;44m commiting changes in %s at %s \033[0m" % (self.annex.name,path))
		
		# early exit in case of no uncommited changes
		if not self.hasUncommitedChanges():
			print("no changes")
			return

		# call 'git-annex add'
		self.execute_command(["git-annex","add"])
		
		# commit it
		utc = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")
		msg = "Host: %s UTC: %s" % (self.host.name,utc)
		try:
			self.execute_command(["git","commit","-m",msg])
		except subprocess.CalledProcessError:
			pass

	def sync(self, annex_descs=None):
		"""
			calls finalise and git-annex sync, when annex_descs (list of annex
			# descriptions) is given, use this list instead of hosts with an active annex
		"""
		# change into the right directory
		path = self.changePath()

		self.finalise()
		
		self.repairMaster()
		
		print("\033[1;37;44m syncing %s \033[0m" % (self.annex.name,))
		
		# if a list of hosts is not given
		if annex_descs is None:
			annex_descs = {repo.description for repo in self.activeRepositories().keys()}
		
		# call 'git-annex sync'
		if annex_descs:
			self.execute_command(["git-annex","sync"] + list(annex_descs))
		else:
			# if no other annex is available, still do basic maintanence
			self.execute_command(["git-annex","merge"])
		
	
	def repairMaster(self):
		""" creates the master branch if necessary """
		
		# change into the right directory
		path = self.changePath()

		branches = self.gitBranches()
		# unneeded, if the master branch already exists
		if "master" in branches:
			return
		
		if "synced/master" in branches:
			# use the 'synced/master' branch if possible
			print("\033[1;37;44m repairing master branch in %s at %s \033[0m" % (self.annex.name,path))
			
			# checkout synced/master
			self.execute_command(["git","checkout","synced/master"])
			
			# create the master branch and check it put
			self.execute_command(["git","branch","master"])
			self.execute_command(["git","checkout","master"])
		else:
			# no we have a problem, we have to create a master branch but do not have
			# many opportunities, use this:
			# 'git commit --allow-empty -m "empty commit"'
			self.execute_command(["git","commit","--allow-empty","-m","empty commit"])
	
	def copy(self, annex_descs=None, files=None, strict=None):
		"""
			copy files, arguments:
			- annex_descs: target machines, if not specified all online machines are used
			- files: expression which specifies which files should be transfered,
			         defaults to the local repositories files entry, if nothing is given,
			         all files are transfered
			- strict: drop all files which do not match the local files expression
		"""
		
		# use files expression of the current repository, if none is given
		if files is None:
			files = self.files
		# parse files expression
		files = self.sanitiseFilesExpression(files)
		files = self.tokeniseFileExpression(files)
		cur_files_cmd = self.tokenisedFilesExpressionToCmd(files)

		# check files expression
		self.checkFilesExpression(cur_files_cmd)
		

		# change into the right directory
		path = self.changePath()

		# get active repositories
		repos = self.activeRepositories()
		
		if annex_descs is not None:
			# remove all with wrong description
			for repo in list(repos.keys()):
				if repo.description not in annex_descs:
					del repos[repo]
		
		# check remote files expression
		for repo in sorted(repos.keys(),key=lambda k:str(k)):
			self.checkFilesExpression(repo.files)
		
		# sync
		self.sync(annex_descs)
		
		print("\033[1;37;44m copying files %s \033[0m" % (self.annex.name,))
		
		
		#
		# pull
		#
		
		# call 'git-annex copy --from=target <files expression as command>'
		for repo in sorted(repos.keys(),key=lambda k:str(k)):
			cmd = ["git-annex","copy","--from=%s"%repo.description] + cur_files_cmd
			self.execute_command(cmd)
	
	
		#
		# push
		#
		
		for repo in sorted(repos.keys(),key=lambda k:str(k)):
			# parse remote files expression
			files = self.sanitiseFilesExpression(repo.files)
			files = self.tokeniseFileExpression(files)
			files_cmd = self.tokenisedFilesExpressionToCmd(files)

			# call 'git-annex copy --to=target <files expression as command>'
			cmd = ["git-annex","copy","--to=%s"%repo.description] + files_cmd
			self.execute_command(cmd)
		
		
		#
		# apply strict
		#
		
		# use strict of the current repository, if none is given
		if strict is None:
			strict = self.strict

		if strict:
			# call 'git-annex drop --not -( <files expression -)
			cmd = ["git-annex","drop"] + ["--not", "-("] + cur_files_cmd + ["-)"]
			self.execute_command(cmd, ignoreexception=True)
		
		# apply strict for remote repositories
		for repo in sorted(repos.keys(),key=lambda k:str(k)):
			# only apply if wanted
			if not repo.strict:
				continue
			# parse remote files expression
			files = self.sanitiseFilesExpression(repo.files)
			files = self.tokeniseFileExpression(files)
			files_cmd = self.tokenisedFilesExpressionToCmd(files)

			# call 'git-annex drop --from=target --not -( <files expression> -)
			cmd = ["git-annex","drop","--from=%s"%repo.description] + ["--not", "-("] + files_cmd + ["-)"]
			self.execute_command(cmd, ignoreexception=True)

		# sync again
		self.sync(annex_descs)

		
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


