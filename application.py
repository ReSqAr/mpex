import os.path
import io
import subprocess

import structure_host
import structure_annex
import structure_repository
import structure_connection

#
# check python version
#
import sys
if sys.version_info<(3,2,0):
        raise RuntimeError("Python version >= 3.2 is needed.")




class Application:
	def __init__(self, path):
		# save option
		self.path = path
		
		# initialise hosts
		self.hosts = structure_host.Hosts(self)
		# initialise annexes
		self.annexes = structure_annex.Annexes(self)
		# initialise repositories
		self.repositories = structure_repository.Repositories(self)
		# initialise connections
		self.connections = structure_connection.Connections(self)
		
		# post load checks
		self.repositories.check()
	
	def save(self):
		""" saves all data """
		self.hosts.save()
		self.annexes.save()
		self.repositories.save()
		self.connections.save()
		
	def currentHost(self):
		""" get the current host """
		# compute path
		path = os.path.join(self.path,"current_hostname")
		# if the path does not exist
		if not os.path.isfile(path):
			raise RuntimeError("Unable to find the current host.")
		with io.open(path, mode="rt", encoding="UTF8") as fd:
			# read
			host = fd.read()
			host = host.strip()
			# associate host to a Host object
			host = self.hosts.get(host)
			# if we failed, raise an error
			if host is None:
				raise RuntimeError("Unable to find the current host.")
			# otherwise, return the found host
			return host
	
	def setCurrentHost(self, host):
		""" set the current host """
		# compute path
		path = os.path.join(self.path,"current_hostname")
		with io.open(path, mode="wt", encoding="UTF8") as fd:
			# write
			fd.write(host.name)
	
	def getHostedRepositories(self):
		""" get all repositories which are hosted on the current machine """
		return self.currentHost().repositories()
	
	
	@property
	def gitAnnexCapabilities(self):
		"""
			checks if the current git annex version supports certain
			operations, e.g. direct mode, certain special remotes, etc.
		"""
		
		# if there is a cache, use it
		if hasattr(self,"_gitAnnexCapabilities_Cache"):
			return self._gitAnnexCapabilities_Cache
		
		capabilities = {}
		
		# call git annex
		version_string = subprocess.check_output(["git-annex","version"])
		version_string = version_string.decode("UTF8")
		
		for line in version_string.splitlines():
			# extract the line 'git-annex version: *'
			s = "git-annex version:"
			if s in line:
				capabilities["version"] = line[len(s):].strip()
		
		# parse the version string
		date = capabilities["version"].split('.')[1]
		assert len(date) == 8, "Version string is unexcepted format: %s" % capabilities["version"]
		year,month,day = date[:4],date[4:6],date[6:]
		year,month,day = int(year),int(month),int(day)
		date = capabilities["date"] = year,month,day
		
		# if the current git annex version is newer than the 2013-04-01 version,
		# it supports direct mode (this date is just a guess)
		capabilities["direct"] = ( date >= (2013,4,1) )
		
		# cache it
		self._gitAnnexCapabilities_Cache = capabilities
		
		# return
		return capabilities