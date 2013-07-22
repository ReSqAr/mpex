import json
import os
import os.path
import io



class Collection:
	def __init__(self, app, filename, cls):
		# save options
		self.app = app
		self.cls = cls
		# compute the file name
		self._path = os.path.join(self.app.path,filename)
		# internal dictionary which tracks all known objects
		self._objects = {}
		# load objects
		self.load()
	
	def load(self):
		""" loads all known objects """
		# clear tracker
		self._objects.clear()
		if os.path.isfile(self._path):
			# open the file if it exists
			with io.open(self._path, mode="rt", encoding="UTF8") as fd:
				# decode list of hosts (json file)
				list_of_objects = json.load(fd)
				# create individual hosts
				for obj in list_of_objects:
					# covert raw object data
					obj = self.rawDataToArgDict(obj)
					# create the object
					self.create(**obj)
	
	def save(self):
		""" saves all known hosts """
		# get set of all known objects
		list_of_objects = list(self._objects.items())
		# convert it to a sorted list of raw data elements
		list_of_objects.sort(key=lambda kv:kv[0])
		list_of_objects = [self.objToRawData(kv[1]) for kv in list_of_objects]

		# open the file in write mode
		with io.open(self._path, mode="wt", encoding="UTF8") as fd:
			# dump data
			json.dump(list_of_objects, fd, ensure_ascii=False, indent=4, sort_keys=True)
	
	def getAll(self):
		""" return all known objects """
		return set(self._objects.values())

	def get(self, *args, **kwargs):
		"""
			get the given object, signature matches the signature of cls, however
			not all data has to specified, only the arguments are needed which are
			required to the deduce the key. if the object does not exists, None is
			returned
		"""
		# compute key
		key = self.keyFromArguments(*args, **kwargs)
		# return object
		return self._objects.get(key)

	def create(self, *args, **kwargs):
		""" get the given object, signature matches the signature of cls """
		# compute key
		key = self.keyFromArguments(*args, **kwargs)
		# if an object with the given key does not yet exists, create it
		if key not in self._objects:
			self._objects[key] = self.cls(self.app,*args,**kwargs)
		# return object
		return self._objects[key]
		
	# virtual methods
	def keyFromArguments(self, *args, **kwargs):
		""" get the key from the arguments """
		raise NotImplementedError
	def objToRawData(self, obj):
		""" converts an object into raw data """
		raise NotImplementedError
	def rawDataToArgDict(self, raw):
		""" brings obj into a form which can be consumed by cls """
		raise NotImplementedError
	
class Hosts(Collection):
	""" tracks all known hosts """
	def __init__(self, app):
		# call super
		super(Hosts,self).__init__(app,"known_hosts",Host)

	def keyFromArguments(self, name):
		""" get the key from the arguments """
		return name
	def objToRawData(self, obj):
		""" converts an object into raw data """
		return {"name": obj.name}
	def rawDataToArgDict(self, raw):
		""" brings obj into a form which can be consumed by cls """
		return {"name": raw["name"]}
		
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
 
 
 

class Annexes(Collection):
	""" tracks all known annexes """
	def __init__(self, app):
		# call super
		super(Annexes,self).__init__(app,"known_annexes",Annex)

	def keyFromArguments(self, name):
		""" get the key from the arguments """
		return name
	def objToRawData(self, obj):
		""" converts an object into raw data """
		return {"name": obj.name}
	def rawDataToArgDict(self, raw):
		""" brings obj into a form which can be consumed by cls """
		return {"name": raw["name"]}
	
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
 

class Repositories(Collection):
	""" tracks all known repositories """
	def __init__(self, app):
		# call super
		super(Repositories,self).__init__(app,"known_repositories",Repository)

	def keyFromArguments(self, host, annex, path, data={}):
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
		# extract host,annex and path
		host = raw.pop("host")
		annex = raw.pop("annex")
		path = raw.pop("path")
		# convert host and annex
		host  = self.app.hosts.create(host)
		annex = self.app.annexes.create(annex)
		# build dictionary
		return {"host":host,"annex":annex,"path":path,"data":raw}

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
		assert self.trust in ("semitrust","trust","untrust")
		
		# sanitise the files expression
		self.sanitiseFilesExpression()
	
	def sanitiseFilesExpression(self):
		""" sanitise the files expression """
		
		# get attribute
		files = self._data.get("files")
		# if there is nothing to do, leave
		if files is None:
			return
		
		# TODO
		
	@property
	def direct(self):
		""" determines if the repository should be in direct mode, default: False """
		return bool(self._data.get("direct",False))
	
	@property
	def files(self):
		""" determines which files should be kept in the repository, default: None """
		return self._data.get("files")
	
	@property
	def strict(self):
		""" determines if ONLY files which match the files epxression should be kept, default: False """
		return self._data.get("strict",False)
	
	@property
	def trust(self):
		""" gives the trust level of the repository, default: semitrust """
		return self._data.get("trust","semitrust")


	def __repr__(self):
		return "Repository(%r,%r,%r,%r)" % (self._host,self._annex,self._path,self._data)

	def __str__(self):
		return "Repository(%s@%s:%s:%s)" % (self._annex.name,self._host.name,self._path,self._data)


class Connections(Collection):
	""" tracks all known connections """
	def __init__(self, app):
		# call super
		super(Connections,self).__init__(app,"known_connections",Connection)

	def keyFromArguments(self, source, dest, path, data={}):
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
		# extract host,annex and path
		source = raw.pop("source")
		dest = raw.pop("dest")
		path = raw.pop("path")
		# convert host and annex
		source = self.app.hosts.create(source)
		dest = self.app.hosts.create(dest)
		# build dictionary
		return {"source":source,"dest":dest,"path":path,"data":raw}

class Connection:
	""" encodes information of one connection """
	def __init__(self, app, source, dest, path, data):
		# save options
		self.app = app
		self._source = source
		self._dest = dest
		self._path = path
		self._data = data
		
		# sanity check: check that we got correct classes and path is valid,
		# path maybe: ssh://<host> or <absolute path>
		assert isinstance(self._dest,Host)
		assert isinstance(self._source,Host)
		assert self._path.startswith("ssh://") or self._path.startswith("/")

	def __repr__(self):
		return "Connection(%r,%r,%r,%r)" % (self._source,self._dest,self._path,self._data)

	def __str__(self):
		return "Connection(%s->%s:%s:%s)" % (self._source.name,self._dest.name,self._path,self._data)

 