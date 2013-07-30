import collections
import os
import sys
import subprocess
import datetime


class LocalRepository:
	"""
		LocalRepository represents a realisation of a repository
		which can be accessed from app.currentHost()
		
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
	"""
	def __init__(self, repo, connection=None):
		# call super
		super(LocalRepository,self).__init__()

		# save options
		self.repo = repo
		self.connection = connection

		# check that the gurantees are valid, i.e. it is reachable via 
		if self.connection:
			# if it is a remote repository, check the integrity of the arguments
			assert self.app.currentHost() == self.connection.source,\
					"the connection does not originate from the current host. (%s != %s)" % (self.app.currentHost(),self.connection.source)
			# the connection should end at the host of the current repository
			assert repo.host == connection.dest,\
					"the connection does not end at the host of the current repository. (%s != %s)" % (self.repo.host,self.connection.dest)
			# the connection has to be local
			assert self.connection.isLocal(),\
					"the connection has to be to 'local'."
		else:
			# otherwise, the repository is hosted on the current host
			assert self.app.currentHost() == self.repo.host,\
					"the repository is not hosted on the current host. (%s != %s)" % (self.app.currentHost(),self.repo.host)
			
	
	def __getattribute__(self, name):
		""" forward request to self.repo """
		try:
			# try to satisfy the request via self.repo
			return getattr(self.repo,name)
		except:
			# otherwise, satisfy the request locally
			return super(LocalRepository,self).__getattribute__(name)
	
	def __setattr__(self, name, v):
		""" forward request to self.repo """
		try:
			# if repo has a variable called name, then set it there
			if hasattr(self.repo,name):
				return setattr(self.repo,name,v)
		except AttributeError:
			# no attribute named repo
			pass
		# otherwise, set it here
		return super(LocalRepository,self).__setattr__(name,v)
	
	@property
	def localpath(self):
		""" returns the path on the local machine """
		if self.connection is None:
			# the repository is on the local machine
			return self.path
		else:
			# we are working remotely: give the path on the local machine
			return self.connection.pathOnSource(self.path)
	
	#
	# file system interaction
	#
	def executeCommand(self, cmd, ignoreexception=False):
		""" print and execute the command """
		
		# use the method given by the application
		self.app.executeCommand(cmd, ignoreexception=ignoreexception)

	def changePath(self, create=False):
		"""
			change the path to the current repository
		"""

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
		self.changePath()

		# call 'git status -s'
		output = subprocess.check_output(["git","status","-s"]).decode("UTF8").strip()
		for line in output.splitlines():
			# we have to ignore lines which start with T
			if line.strip().startswith("T"):
				continue
			# we have found a valid line
			return True
		else:
			# nothing to do
			return False
	
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
		return self.readGitKey("annex.uuid", )
	
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



	#
	# main methods
	#
	def init(self, ignorenonempty=False):
		""" inits the repository """
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print("\033[1;37;44m initialise %s at %s \033[0m" % (self.annex.name,self.localpath))

		# change into the right directory, create it if necessary
		self.changePath(create=True)
		
		# init git
		if not os.path.isdir(os.path.join(self.localpath,".git")):
			if os.listdir(self.localpath) and not ignorenonempty:
				raise RuntimeError("Trying to run 'git init' in a non-empty directory, set ignorenonempty=True.")
			else:
				self.executeCommand(["git","init"])
		else:
			if self.app.verbose <= self.app.VERBOSE_NORMAL:
				print("It is already a git repository.")
		
		# init git annex
		if not os.path.isdir(os.path.join(self.localpath,".git/annex")):
			self.executeCommand(["git-annex","init",self.description])
		else:
			if self.app.verbose <= self.app.VERBOSE_NORMAL:
				print("It is already a git annex repository.")
		
		# set the properties
		self.setProperties()
	
	def setProperties(self):
		""" sets the properties of the current repository """
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print("\033[1;37;44m setting properties of %s at %s \033[0m" % (self.annex.name,self.localpath))
		
		# change into the right directory
		self.changePath()

		# set the requested direct mode, if doable
		if self.app.gitAnnexCapabilities["direct"]:
			# change only if needed
			d = "direct" if self.direct else "indirect"
			if self.onDiskDirectMode() != d:
				self.executeCommand(["git-annex",d])
		else:
			if self.direct:
				if self.app.verbose <= self.app.VERBOSE_NORMAL:
					print("direct mode is requested, however it is not supported by your git-annex version.")
		
		# set trust level if necessary
		if self.onDiskTrustLevel() != self.trust:
			self.executeCommand(["git-annex",self.trust,"here"])
		
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
				url = self.readGitKey("remote.%s.url" % gitID, )
			except subprocess.CalledProcessError:
				# no url was yet set
				url = None
			
			if not url:
				# if no url was yet set, set it
				self.executeCommand(["git","remote","add",gitID,gitPath])
			else:
				# otherwise, check that the correct one has been set
				if url != gitPath:
					raise RuntimeError("The url set for the connection %s does not match the computed one." % connection)
				else:
					continue
	
	def finalise(self):
		""" calls git-annex add and commits all changes """
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print("\033[1;37;44m commiting changes in %s at %s \033[0m" % (self.annex.name,self.localpath))
		
		# change into the right directory
		self.changePath()

		# early exit in case of no uncommited changes
		if not self.hasUncommitedChanges():
			if self.app.verbose <= self.app.VERBOSE_NORMAL:
				print("no changes")
			return

		# call 'git-annex add'
		self.executeCommand(["git-annex","add"])
		
		# commit it
		utc = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")
		msg = "Host: %s UTC: %s" % (self.host.name,utc)
		try:
			# WARNING: never think of -am
			self.executeCommand(["git","commit","-m",msg])
		except subprocess.CalledProcessError:
			pass

	def sync(self, annex_descs=None):
		"""
			calls finalise and git-annex sync, when annex_descs (list of annex
			descriptions) is given, use this list instead of hosts with an active annex
		"""
		self.finalise()
		
		self.repairMaster()
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print("\033[1;37;44m syncing %s in %s \033[0m" % (self.annex.name,self.localpath))
		
		# change into the right directory
		self.changePath()

		# if a list of hosts is not given
		if annex_descs is None:
			annex_descs = {repo.description for repo in self.activeRepositories().keys()}
		
		if annex_descs:
			# call 'git-annex sync'
			self.executeCommand(["git-annex","sync"] + list(annex_descs))
		else:
			# if no other annex is available, still do basic maintanence
			self.executeCommand(["git-annex","merge"])
		
	
	def repairMaster(self):
		""" creates the master branch if necessary """
		
		# change into the right directory
		self.changePath()

		branches = self.gitBranches()
		# unneeded, if the master branch already exists
		if "master" in branches:
			return
		
		if "synced/master" in branches:
			# use the 'synced/master' branch if possible
			if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
				print("\033[1;37;44m repairing master branch in %s at %s \033[0m" % (self.annex.name,self.localpath))
			
			# checkout synced/master
			self.executeCommand(["git","checkout","synced/master"])
			
			# create the master branch and check it put
			self.executeCommand(["git","branch","master"])
			self.executeCommand(["git","checkout","master"])
		else:
			# no we have a problem, we have to create a master branch but do not have
			# many opportunities, use this:
			# 'git commit --allow-empty -m "empty commit"'
			self.executeCommand(["git","commit","--allow-empty","-m","empty commit"])
	
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
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print("\033[1;37;44m copying files %s at %s \033[0m" % (self.annex.name,self.localpath))
		
		# change into the right directory
		self.changePath()

		#
		# pull
		#
		
		# call 'git-annex copy --from=target <files expression as command>'
		for repo in sorted(repos.keys(),key=lambda k:str(k)):
			cmd = ["git-annex","copy","--from=%s"%repo.description] + cur_files_cmd
			self.executeCommand(cmd)
	
	
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
			self.executeCommand(cmd)
		
		
		#
		# apply strict
		#
		
		# use strict of the current repository, if none is given
		if strict is None:
			strict = self.strict

		if strict:
			# call 'git-annex drop --not -( <files expression -)
			cmd = ["git-annex","drop"] + ["--not", "-("] + cur_files_cmd + ["-)"]
			self.executeCommand(cmd, ignoreexception=True)
		
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
			self.executeCommand(cmd, ignoreexception=True)

		# sync again
		self.sync(annex_descs, )


	def deleteAllRemotes(self):
		"""
			deletes all remotes found in .git/confing, this implicitly deletes
			also all remote tracking-branches
		"""
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print("\033[1;37;44m delete all remotes of %s in %s\033[0m" % (self.annex.name,self.localpath))

		# change path to current directory
		self.changePath()

		# find all remotes
		cmd = ["git","remote","show"]
		output = subprocess.check_output(cmd).decode("UTF-8")
		remotes = [remote.strip() for remote in output.splitlines()]
		if self.app.verbose <= self.app.VERBOSE_NORMAL:
			print("remotes found: %s" % ', '.join(remotes))
		
		# delete all remotes
		for remote in remotes:
			cmd = ["git","remote","remove",remote]
			self.executeCommand(cmd)
		
		
 
