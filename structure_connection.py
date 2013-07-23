import string
import os.path

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

	@property
	def gitID(self):
		""" specifies the ID used by git to identify the connection """
		# extract git ID
		gitid = self._data.get("gitid")
		# if there was no git id, create a valid one based on the name of dest
		if gitid is None:
			gitid = self.dest.name
		# filter unwanted characters
		VALID_CHARS = set(string.ascii_letters + string.digits)
		gitid = [c for c in gitid if c in VALID_CHARS]
		if not gitid:
			raise ValueError("%s: cannot generate a valid git id." % self)
		# return
		return "".join(gitid)
	
	#
	# derived methods
	#
	def protocol(self):
		""" returns the used protocol """
		if self._path.startswith("/"):
			return "mount"
		elif self._path.startswith("ssh://"):
			return "ssh"
		else:
			raise ValueError("Unknown protocol specified in %s." % self)
	
	def gitPath(self, repo):
		""" computes the path used by git to access the repository over the connection """
		
		assert self.dest == repo.host, "Programming error."
		
		# get the protocol
		protocol = self.protocol()
		
		if protocol == "mount":
			# if the other directory is mounted, then join the paths
			return os.path.join(self.path,repo.path)
		elif protocol == "ssh":
			# if we can connect via ssh, use it
			ssh = self.path
			# kill the trailing /
			if ssh.endswith("/"):
				ssh = ssh[:-1]
			return ssh + repo.path
		else:
			raise ValueError("Programming error.")
		
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

