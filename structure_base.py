import json
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
		list_of_objects.sort(key=lambda kv:str(kv[0]))
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
			required to the deduce the key. if the object does not exists, an error
			is raised
		"""
		# compute key
		key = self.keyFromArguments(*args, **kwargs)
		# return object
		return self._objects[key]

	def create(self, *args, **kwargs):
		""" get the given object, signature matches the signature of cls """
		# compute key
		key = self.keyFromArguments(*args, **kwargs)
		# the object may not exist yet
		assert key not in self._objects, "object with key %s already exists: %s" % (key,self._objects[key])
		# create it
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
 
