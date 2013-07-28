import string
import os
import subprocess

import structure_base
import structure_host


class Connections(structure_base.Collection):
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
		assert isinstance(self._source,structure_host.Host), "%s: source has to be an instance of Host" % self
		assert isinstance(self._dest,structure_host.Host), "%s: dest has to be an instance of Host" % self
		assert self.source != self.dest, "%s: source and destination may not agree" % self

		# see if we can find a valid protocol
		self.protocol()

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

	#
	# derived methods
	#
	def pathData(self):
		""" returns a dictionary with all relevant data on the path """
		data = {}
		
		if self._path.startswith("/"):
			data["protocol"] = "mount"
		elif self._path.startswith("ssh://"):
			data["protocol"] = "ssh"
			data["server"] = self._path[len("ssh://"):]
		else:
			raise ValueError("Unknown protocol specified in %s." % self)

		assert "protocol" in data, "Programming error"
		return data
		
	def protocol(self):
		""" returns the used protocol """
		return self.pathData()["protocol"]
	
	def gitPath(self, repo):
		""" computes the path used by git to access the repository over the connection """
		
		assert self.dest == repo.host, "Programming error."
		
		# get the protocol
		protocol = self.protocol()
		
		if protocol in ("mount","ssh"):
			# if we it is mounted or we can connect via ssh, just join them together
			path = self.path
			# kill the trailing /
			if path.endswith("/"):
				path = path[:-1]
			return path + repo.path
		else:
			raise ValueError("Programming error.")
	
	def isOnline(self):
		""" checks if the connection is online """
		# if always on is set, then the connection is online
		if self.alwaysOn:
			return True
		
		# if there is a cache, use it
		if hasattr(self,"_isonline_cache"):
			return self._isonline_cache

		
		# get data
		data = self.pathData()
		
		if data["protocol"] == "mount":
			# consider a path mounted if the directory exists and is non-empty
			if os.path.isdir(self.path) and os.listdir(self.path):
				isonline = True
			else:
				isonline = False
		elif data["protocol"] == "ssh":
			try:
				# run 'ssh <server> echo test'
				print("checking ssh connection to server '%s'... "%data["server"],end="")
				with open(os.devnull, "w") as devnull:
					subprocess.check_output(["ssh",data["server"],"echo","test"],stderr=devnull)
				# if it succeeds, say the connection is online
				isonline = True
				print("online")
			except subprocess.CalledProcessError:
				# otherwise, it is not only
				isonline = False
				print("offline")
		else:
			raise ValueError("Programming error.")
		
		# cache it
		self._isonline_cache = isonline
		# return status
		return isonline

	def isLocal(self):
		"""
			is the connection local, i.e. something which can be
			reached via the file system
		"""
		# a connection is local if it is of type 'mount'
		return self.protocol() in ("mount",)

	def pathOnSource(self, path):
		"""
			assume that path is path on self.dest and that the connection is of
			type mount, the return value is the path on self.source
		"""
		assert self.isLocal(), "Incorrect usage."
		
		# kill the trailing /
		prefix = self.path
		if prefix.endswith("/"):
			prefix = prefix[:-1]
		# just join them together
		return prefix + path

	#
	# hashable type mehods, hashable is needed for dict keys and sets
	# (source: http://docs.python.org/2/library/stdtypes.html#mapping-types-dict)
	#
	def __hash__(self):
		return hash((self.source,self.dest,self.path))
	
	def __eq__(self, other):
		return (self.source,self.dest,self.path) == (other.source,other.dest,other.path)

	def __repr__(self):
		return "Connection(%r,%r,%r,%r)" % (self._source,self._dest,self._path,self._data)

	def __str__(self):
		return "Connection(%s->%s:%s:%s)" % (self._source,self._dest,self._path,self._data)

