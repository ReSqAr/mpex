import json
import os
import os.path
import io

#
# check python version
#
import sys
if sys.version_info<(3,2,0):
        raise RuntimeError("Python version >= 3.2 is needed.")


class Hosts:
	""" tracks all known hosts """
	FILENAME = "known_hosts"
	def __init__(self, path):
		# save option
		self._path = path
		# compute the file name
		self._hostspath = os.path.join(self._path,self.FILENAME)
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
			# convert to string
			s = json.dumps(hostNames, ensure_ascii=False, indent=4, sort_keys=True)
			# dump data
			fd.write(unicode(s))
	
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
			host = Host(name)
			self._hosts[name] = host
		
		# return the found (or created) host
		return self._hosts[name]
		
class Host:
	""" encodes information of one host """
	def __init__(self, name):
		# save option
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
	def __init__(self, path):
		# save option
		self._path = path
		# compute the file name
		self._annexespath = os.path.join(self._path,self.FILENAME)
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
			# convert to string
			s = json.dumps(annexNames, ensure_ascii=False, indent=4, sort_keys=True)
			# dump data
			fd.write(unicode(s))
	
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
			annex = Annex(name)
			self._annexes[name] = annex
		
		# return the found (or created) annex
		return self._annexes[name]
		
class Annex:
	""" encodes information of one annex """
	def __init__(self, name):
		# save option
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
 
