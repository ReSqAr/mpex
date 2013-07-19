import json
import os
import os.path
import io

class Hosts:
	""" tracks all known hosts """
	FILENAME = "known_hosts"
	def __init__(self, app):
		# save option
		self.app = app
		# compute the file name
		self._hostspath = os.path.join(self.app.path,self.FILENAME)
		# internal dictionary which tracks all known hosts
		self._hosts = {}
		# load hosts
		self.load()
	
	def load(self):
		""" loads all known hosts """
		if os.path.isfile(self._hostspath):
			# open the file if it exists
			with io.open(self._hostspath, mode="rt", encoding="UTF8") as fd:
				# decode list of hosts (json file)
				list_of_hosts = json.load(fd)
				# create individual hosts
				for host in list_of_hosts:
					self.getHost(host)
	
	def save(self):
		""" saves all known hosts """
		# get set of all known host names
		hostNames = self.allHostNames()
		# convert it to a sorted list
		hostNames = list(sorted(hostNames))

		# open the file in write mode
		with io.open(self._hostspath, mode="wt", encoding="UTF8") as fd:
			# dump data
			json.dump(hostNames, fd, ensure_ascii=False, indent=4, sort_keys=True)
	
	def allHostNames(self):
		""" return all known host names """
		return set(self._hosts.keys())
	
	def allHosts(self):
		""" return all known hosts """
		return set(self._hosts.values())

	def getHost(self, name):
		""" get the given host """

		if name not in self._hosts:
			# if the we do not have yet a host with the given name, create one
			host = Host(self.app,name)
			self._hosts[name] = host
		
		# return the found (or created) host
		return self._hosts[name]
		
class Host:
	""" encodes information of one host """
	def __init__(self, app, name):
		# save options
		self.app = app
		self._name = name
	
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
 
 
 

class Annexes:
	""" tracks all known annexes """
	FILENAME = "known_annexes"
	def __init__(self, app):
		# save option
		self.app = app
		# compute the file name
		self._annexespath = os.path.join(self.app.path,self.FILENAME)
		# internal dictionary which tracks all known annexes
		self._annexes = {}
		# load annexes
		self.load()
	
	def load(self):
		""" loads all known annexes """
		if os.path.isfile(self._annexespath):
			# open the file if it exists
			with io.open(self._annexespath, mode="rt", encoding="UTF8") as fd:
				# decode list of annexes (json file)
				list_of_annexes = json.load(fd)
				# create individual annexes
				for annex in list_of_annexes:
					self.getAnnex(annex)
	
	def save(self):
		""" saves all known annexes """
		# get set of all known annex names
		annexNames = self.allAnnexNames()
		# convert it to a sorted list
		annexNames = list(sorted(annexNames))

		# open the file in write mode
		with io.open(self._annexespath, mode="wt", encoding="UTF8") as fd:
			# dump data
			json.dump(annexNames, fd, ensure_ascii=False, indent=4, sort_keys=True)
	
	def allAnnexNames(self):
		""" return all known annex names """
		return set(self._annexes.keys())
	
	def allAnnexes(self):
		""" return all known annexes """
		return set(self._annexes.values())

	def getAnnex(self, name):
		""" get the given annex """

		if name not in self._annexes:
			# if the we do not have yet a annex with the given name, create one
			annex = Annex(self.app,name)
			self._annexes[name] = annex
		
		# return the found (or created) annex
		return self._annexes[name]
		
class Annex:
	""" encodes information of one annex """
	def __init__(self, app, name):
		# save options
		self.app = app
		self._name = name
	
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
 


class Repositories:
	""" configuration of repositories """
	FILENAME = "known_repositories"
	def __init__(self, app):
		# save option
		self.app = app
		# compute the file name
		self._repopath = os.path.join(self.app.path,self.FILENAME)
		# internal set which tracks all known configurations
		self._repos = {}
		# load configurations
		self.load()
	
	def load(self):
		""" loads all configurations """
		if os.path.isfile(self._repopath):
			# open the file if it exists
			with io.open(self._repopath, mode="rt", encoding="UTF8") as fd:
				# decode list configurations (json file)
				list_of_repos = json.load(fd)
				# create configurations
				for host, annex, path, data in list_of_repos:
					# find host and annex
					host  = self.app.hosts.getHost(host)
					annex = self.app.annexes.getAnnex(annex)
					# create config
					self.getRepository(host, annex, path, data)
	
	def save(self):
		""" saves all repositories """
		# get all known configurations
		configs = self.allRepositories()
		# convert it to a list
		configs = [(c._host.name,c._annex.name,c._path,c._data) for c in configs]
		# sort it
		configs.sort()

		# open the file in write mode
		with io.open(self._repopath, mode="wt", encoding="UTF8") as fd:
			# dump data
			json.dump(configs, fd, ensure_ascii=False, indent=4, sort_keys=True)
	
	def allRepositories(self):
		""" return all known repositories """
		return set(self._repos.values())

	def getRepository(self, host, annex, path, data):
		""" creates a repository with the given parameters """
		# compute key
		key = (host,path)
		
		if key not in self._repos:
			# if the we do not have yet a repository  the given key, create one
			config = Repository(self.app, host, annex, path, data)
			self._repos[key] = config
		
		# return the found (or created) config
		return self._repos[key]

class Repository:
	""" one repository """
	def __init__(self, app, host, annex, path, data):
		# save options
		self.app = app
		self._host = host
		self._annex = annex
		self._path = path
		self._data = data
		
		# sanity check: check that we got correct classes and path is absolute
		assert isinstance(self._host,Host)
		assert isinstance(self._annex,Annex)
		assert self._path.startswith("/")

	def __repr__(self):
		return "Repository(%r,%r,%r,%r)" % (self._host,self._annex,self._path,self._data)

	def __str__(self):
		return "Repository(%s@%s:%s:%s)" % (self._annex.name,self._host.name,self._path,self._data)
