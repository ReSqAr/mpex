import collections
import os
import sys
import string
import subprocess
import datetime

import application

from lib.terminal import print_blue, print_red


class GitRepository:
	
	@property
	def localpath(self):
		raise NotImplementedError
	
	#
	# file system interaction
	#
	def executeCommand(self, cmd, ignoreexception=False):
		""" print and execute the command """
		
		# use the method given by the application
		self.app.executeCommand(cmd, ignoreexception=ignoreexception)


	def changePath(self, create=False):
		""" change the path to the current repository """

		# get path
		path = os.path.normpath(self.localpath)
		
		if create:
			# create the path if needed
			if not os.path.isdir(path):
				os.makedirs(path)
		elif not os.path.isdir(os.path.join(path,".git/annex")):
			# if we are not allowed to create it, it has to be git annex archive
			print_red("%s is not a git annex repository, please run 'mpex init' first." % path,sep='')
			raise application.InterruptedException("this is not a git annex repository")
			
		# change to it
		os.chdir(path)
		
		# make really sure that we are, where we want to be
		assert os.path.normpath(os.getcwd()) == path, "We are in the wrong directory?!?"
		
		return path
		
	def gitConfig(self, key):
		""" read a git key """
		# change path
		self.changePath()
		
		# get output of 'git config $key' and return it
		output = subprocess.check_output(["git","config",key]).decode("UTF-8").strip()
		assert output, "Error."
		return output
	
	def gitBranch(self):
		""" returns all known branches """
		# change path
		self.changePath()

		# call 'git branch'
		output = subprocess.check_output(["git","branch"]).decode("UTF8")
		# the first two characters are noise
		return [line[2:].strip() for line in output.splitlines() if line.strip()]

	def gitDiff(self, filter=None, staged=False):
		"""
			calls 'git diff', with the given filter command and is
			looking on staged files, if requested, returns with a
			dictionary filename -> status
		"""
		# change into the right directory
		self.changePath()

		# the option -z is used to get NULL terminated strings
		cmd = ["git","diff","-z","--name-status"]
		# append filter statement
		if filter is not None:
			cmd.append("--diff-filter=%s"%filter)
		# only staged files?
		if staged:
			cmd.append("--cached")
		
		# call 'git diff'
		output = subprocess.check_output(cmd).decode("UTF-8")
		data = output.split("\0")

		# data looks like: <state>, <filename>, ..., ''
		assert len(data) % 2 == 1, "git diff output has an unusual format"

		return {filename: state for state,filename in zip(data[::2],data[1::2])}
		
	def gitStatus(self):
		""" call 'git status' """
		# change into the right directory
		self.changePath()

		# the option -z is used to get NULL terminated strings
		cmd = ["git","status","-z","--porcelain"]
		
		# call 'git diff'
		output = subprocess.check_output(cmd).decode("UTF-8")
		data = output.split("\0")

		# data looks like: <state><state><space><filename>, ..., ''
		return {d[3:]:d[:2].strip() for d in data if d}

	def gitHead(self):
		""" get the git HEAD of the master branch """
		path = os.path.join(self.localpath,".git/refs/heads/master")
		with open(path,"rt") as fd:
			return fd.read()
	
	def gitRemotes(self):
		""" find all git remotes """
		
		# change into the right directory
		self.changePath()
		
		# read all remotes
		cmd = ["git","remote","show"]
		output = subprocess.check_output(cmd).decode("UTF-8")
		return {remote.strip() for remote in output.splitlines()}
		
	
	def isStageNonEmpty(self):
		""" are there any staged files? """
		return bool(self.gitDiff(staged=True))
	
	def deletedFiles(self):
		""" get the deleted files """
		return list(self.gitDiff(filter="D").keys())
	
	def hasUncommitedChanges(self):
		"""
			has the current repository uncommited changes?
			warning: hasUncommitedChanges is inaccurate for direct
			         repositories as a type change can mask a content change
		"""
		# accept all except type changes
		return any(status != 'T' for status in self.gitStatus().values())


class GitAnnexRepository(GitRepository):
	def standardRepositories(self):
		raise NotImplementedError
	
	def gitAnnexStatus(self):
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
				# check that the line has the right form
				assert ':' in line, "git annex status malformed: '%s'" % line
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
				key = "%s | list" % lastkey
				
				# create the list if necessary
				if key not in status:
					status[key] = []
				
				# append the current line
				status[key].append(line.strip())
		
		return status
		
	def getAnnexUUID(self):
		""" get the git annex uuid of the current repository """
		return self.gitConfig("annex.uuid")
	
	def onDiskDirectMode(self):
		""" finds the on disk direct mode """
		
		# if the current version does not have direct mode capability, return indirect
		if not self.app.gitAnnexCapabilities["direct"]:
			return "indirect"
		
		# get git annex status
		status = self.gitAnnexStatus()
		
		# read the mode
		assert "repository mode" in status, "Invalid git-annex output"
		mode = status["repository mode"]
		assert mode in ("direct","indirect"), "Unknown direct mode detected: %s" % mode
		return mode

	def onDiskTrustLevel(self):
		""" determines the current trust level """

		# get git annex status and git annex uuid
		uuid = self.getAnnexUUID()
		status = self.gitAnnexStatus()
		
		for level in self.TRUST_LEVEL:
			# create key
			key = "%sed repositories | list" % level
			
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

	def onDiskDescription(self):
		""" find the on disk description of the current repository """
		""" determines the current trust level """

		# get git annex status and git annex uuid
		uuid = self.getAnnexUUID()
		status = self.gitAnnexStatus()
		
		for level in self.TRUST_LEVEL:
			# create key
			key = "%sed repositories | list" % level
			
			# if there is repository on the current trust level, ignore it
			if key not in status:
				continue
			
			# read the list of repositories, format: UUID -- name
			repos = status[key]
			
			for repo in repos:
				# find the repository with our current uuid
				if repo.startswith(uuid):
					# format: uuid -- here (<repo name>)
					return repo.strip().split("here (",1)[1][:-1]
		else:
			raise ValueError("Unable to determine the current description.")

	def missingGitRemotesCheck(self, repos):
		""" check that all given repositories are indeed registered as a git remote """
		# get registered git remotes
		remotes = self.gitRemotes()
		
		# compute the missing ones
		missing = {r for r in repos if r.gitID() not in remotes}
		
		# if none are missing, everything is alright
		if not missing:
			return
		
		# otherwise warn the user
		print_red("the following repositories are not registered, consider running 'mpex reinit'", sep='')
		for r in sorted(missing, key=lambda r: str((r.host,r.annex,r.path))):
			print("Host: %s Annex: %s Path: %s" % (r.host.name,r.annex.name,r.path))
			# there is something additional to be told in the case of special repositories
			if r.isSpecial():
				print_red("warning: this is a special remote, you have to enable it manually", sep='')
				print("create the special remote with the following command:")
				print("    git annex initremote %s mac=HMACSHA512 encryption=<key> type=<type> ..." % r.gitID())
				print("activate an already existing special remote with the following command:")
				print("    git annex enableremote %s" % r.gitID())
				print("NEVER create a special remote twice.")
		
		# bail out
		raise application.InterruptedException("there are missing git remotes")

	#
	# main methods
	#
	def init(self, ignorenonempty=False):
		""" inits the repository """
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print_blue("initialise", self.annex.name, "at", self.localpath)

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
			print_blue("setting properties of", self.annex.name, "at", self.localpath)
		
		# change into the right directory
		self.changePath()

		# set the description, if needed
		if self.onDiskDescription() != self.description:
			cmd = ["git-annex","describe","here",self.description]
			self.executeCommand(cmd)

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
		for repo, connections in self.standardRepositories().items():
			# ignore special repositories
			if repo.isSpecial():
				continue
			
			# make sure that we have only one connection
			assert connections, "Programming error."
			assert len(connections) == 1, "Git supports only up to one connection."
			
			# select connection and get details
			connection = connections.pop()
			gitID   = repo.gitID()
			# determine the git path
			if connection is None:
				# if it is local, use the path
				gitPath = repo.path
			else:
				# otherwise delegate this question to the connection
				gitPath = connection.gitPath(repo)

			try:
				# determine which url was already set
				url = self.gitConfig("remote.%s.url" % gitID)
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
			print_blue("commiting changes in", self.annex.name, "at", self.localpath)
		
		# change into the right directory
		self.changePath()


		# call 'git-annex add'
		self.executeCommand(["git-annex","add"])
		

		# find deleted files
		deleted = self.deletedFiles()

		if deleted and self.app.verbose <= self.app.VERBOSE_NORMAL:
			print("found %d deleted files, removing them from git"%len(deleted))
		
		# call 'git rm' for every deleted file
		for filename in deleted:
			# check that the file indeed does not exist
			assert not os.path.isfile(os.path.join(self.localpath,filename)), "file '%s' does still exist?" % filename
			# call 'git rm'
			self.executeCommand(['git','rm',filename])
			

		# is anything staged?
		if self.isStageNonEmpty():
			# commit it
			utc = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")
			msg = "Host: %s UTC: %s" % (self.host.name,utc)
			# WARNING: never think of -a
			self.executeCommand(["git","commit","-m",msg])
		else:
			if self.app.verbose <= self.app.VERBOSE_NORMAL:
				print("no changes")

	def sync(self, repositories=None):
		"""
			calls finalise and git-annex sync, when repositories is given, sync
			only with those, otherwise with all connected repositories insted
		"""
		# finalise repository
		self.finalise()
		
		# make sure that the master branch exists
		self.repairMaster()
	
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print_blue("syncing", self.annex.name, "in", self.localpath)
		
		# change into the right directory
		self.changePath()

		# repositories to sync with (select only non-special repositories)
		sync_repos = set(repo for repo in self.standardRepositories().keys() if not repo.isSpecial())

		# check that all these repositories are registered
		self.missingGitRemotesCheck(sync_repos)

		# only select wanted repositories
		if repositories is not None:
			sync_repos &= set(repositories)
		
		if sync_repos:
			# call 'git-annex sync $gitIDs'
			gitIDs = [repo.gitID() for repo in sorted(sync_repos,key=str)]
			self.executeCommand(["git-annex","sync"] + gitIDs)
		else:
			# if no other annex is available, still do basic maintanence
			self.executeCommand(["git-annex","merge"])
		
	
	def repairMaster(self):
		""" creates the master branch if necessary """
		
		# change into the right directory
		self.changePath()

		branches = self.gitBranch()
		# unneeded, if the master branch already exists
		if "master" in branches:
			return
		
		if "synced/master" in branches:
			# use the 'synced/master' branch if possible
			if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
				print_blue("repairing master branch in", self.annex.name, "at", self.localpath)
			
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
	
	
	def copy(self, copy_all=False, repositories=None, files=None, strict=None):
		"""
			copy files, arguments:
			- copy_all: call git annex with the --all flag
			- repositories: target repositories, if the default is given, then all are used
			- files: expression which specifies which files should be transfered,
			         defaults to the local repositories files entry, if nothing is given,
			         all files are transfered
			- strict: drop all files which do not match the local files expression
		"""
		
		# use files expression of the current repository, if none is given
		if files is None:
			local_files_cmd = self.filesAsCmd()
		else:
			local_files_cmd = self._filesAsCmd(files)

		# repositories to copy from and to
		repos = set(self.standardRepositories().keys())

		# check that all these repositories are registered
		self.missingGitRemotesCheck(repos)

		# only select wanted repositories
		if repositories is not None:
			repos &= set(repositories)
		
		# check remote files expression
		for repo in sorted(repos,key=str):
			# if we can convert it to command line arguments, then everything is fine
			repo.filesAsCmd()
		
		# sync
		self.sync(repos)
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print_blue("copying files of", self.annex.name, "at", self.localpath)
		
		# change into the right directory
		self.changePath()

		#
		# pull
		#
		
		# compute flags which should be used:
		#   --fast and --all (if available and wanted)
		# rationale:
		#   --fast: we are synced
		flags = ["--fast"]
		if self.app.gitAnnexCapabilities["all"] and copy_all:
			flags.append("--all")
		
		# call 'git-annex copy --fast [--all] --from=target <files expression as command>'
		for repo in sorted(repos,key=str):
			cmd = ["git-annex","copy"] + flags + ["--from=%s"%repo.gitID()] + local_files_cmd
			self.executeCommand(cmd)
	
	
		#
		# push
		#
		
		for repo in sorted(repos,key=str):
			# parse remote files expression
			files_cmd = repo.filesAsCmd()

			# call 'git-annex copy --fast [--all] --to=target <files expression as command>'
			cmd = ["git-annex","copy"] + flags + ["--to=%s"%repo.gitID()] + files_cmd
			self.executeCommand(cmd)
		
		
		#
		# apply strict
		#
		
		# use strict of the current repository, if none is given
		if strict is None:
			strict = self.strict

		if strict:
			# call 'git-annex drop --not -( <files expression -)
			cmd = ["git-annex","drop"] + ["--not", "-("] + local_files_cmd + ["-)"]
			self.executeCommand(cmd, ignoreexception=True)
		
		# apply strict for remote repositories
		for repo in sorted(repos,key=str):
			# only apply if wanted
			if not repo.strict:
				continue
			# parse remote files expression
			files_cmd = repo.filesAsCmd()

			# call 'git-annex drop --from=target --not -( <files expression> -)
			cmd = ["git-annex","drop","--from=%s"%repo.gitID()] + ["--not", "-("] + files_cmd + ["-)"]
			self.executeCommand(cmd, ignoreexception=True)

		# sync again
		self.sync(repos)


	def deleteAllRemotes(self):
		"""
			deletes all remotes found in .git/confing, this implicitly deletes
			also all remote tracking-branches
		"""
		
		if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
			print_blue("delete all remotes of", self.annex.name, "in", self.localpath)

		# change path to current directory
		self.changePath()

		# find all remotes
		remotes = self.gitRemotes()
		if self.app.verbose <= self.app.VERBOSE_NORMAL:
			print("remotes found: %s" % ', '.join(remotes))
		
		# delete all remotes
		for remote in remotes:
			cmd = ["git","remote","rm",remote]
			self.executeCommand(cmd)





class LocalRepository(GitAnnexRepository):
	"""
		LocalRepository represents a realisation of a repository
		which can be accessed from app.currentHost()
		
		main git annex methods:
			init(ignorenonempty=False)
			setProperties()
			finalise()
			sync(annex descriptions=None)
			repairMaster()
			copy(annex descriptions, files expression, strict=true/false)
			deleteAllRemotes()

		git methods:
			gitConfig(key) -> value
			gitBranch() -> list of branches
			gitDiff(filter=None, staged=False) -> dictionary: filename -> status
			gitStatus() -> dictionary: filename -> status
			gitHead() -> git head
			isStageNonEmpty()
			deletedFiles()
			hasUncommitedChanges() (careful: slightly inaccurate)
		
		git annex methods:
			gitAnnexStatus()
			getAnnexUUID()
			onDiskDirectMode()
			onDiskTrustLevel()
			onDiskDescription()
			
		other methods:
			changePath()
			standardRepositories()
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
		assert not self.isSpecial(), "local path can only be called for non-special remotes"
		
		if self.connection is None:
			# the repository is on the local machine
			return self.path
		else:
			# we are working remotely: give the path on the local machine
			return self.connection.pathOnSource(self.path)
	

	def standardRepositories(self):
		""" determine repositories which are online (from the point of view of the current host) """
		# convert connections to a dictionary dest -> set of connections to dest
		connections = collections.defaultdict(set)
		for connection in self.app.currentHost().connections():
			connections[connection.dest].add(connection)
		
		# add trivial connection from the current host!
		connections[self.host].add(None)
		
		# get repositories
		repositories = self.annex.repositories()
		
		# get the repositories which are online
		active_repos = collections.defaultdict(set)
		
		for repository in repositories:
			# filter out the current repository
			if repository == self:
				continue
			
			for connection in connections[repository.host]:
				if connection is None:
					# we are working locally, add the connection only if
					# the repository is non-special, i.e. avoid implcit
					# connections to special local repositories
					if not repository.isSpecial():
						active_repos[repository].add(connection)
				elif connection.isOnline():
					# add the connection if the connection is online
					active_repos[repository].add(connection)
		
		return active_repos



 
