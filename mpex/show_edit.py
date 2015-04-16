import collections

from .lib import fuzzy_match
from .lib.terminal import print_blue, print_red, print_bold, choose, ask_questions

from . import structure_host
from . import structure_annex
from . import structure_repository



#
# table helper functions
#

def printed_len(s):
	""" computes the printed length of a string s """
	# strip all non-printed characters: \033...m
	while "\033" in s:
		a,b = s.split("\033",1)
		b = b.split("m",1)[1]
		s = a + b
	return len(s)

def print_table(table,sep=2,header_sep="="):
	""" prints a table """
	# empty table -> do nothing
	if not table:
		return
	# number of columns, determined by the first row
	# (has to be constant)
	columns = len(table[0])
	# array which holds the length of the individual columns
	column_lengths = columns * [0]
	# iterate over rows
	for row in table:
		# check that it has the correct number of columns
		assert len(row) == columns, "Programming error."
		# update lengths array
		column_lengths = [max(printed_len(row[i]),column_lengths[i]) for i in range(columns)]
	
	# output
	for i,row in enumerate(table):
		# print header in bold
		if i == 0: print("\033[1m",end="")

		for column_length,item in zip(column_lengths,row):
			# print the item left justified
			print(item,end='')
			print(' '*(column_length + sep - printed_len(item)),end='')

		if i == 0: print("\033[0m",end="")

		# print a new line
		print()

		# the first line is the header
		if i == 0:
			print(header_sep * (sum(column_lengths) + (len(column_lengths)-1) * sep))

def enumerate_table(table):
	""" adds the row number as the first column """
	return [ [str(i-1+1) if i>0 else "n"] + row for i,row in enumerate(table) ]

def format_host(env, host):
	if env.highlightedhost and env.highlightedhost == host:
		return "\033[1m%s\033[0m" % host.name
	else:
		return host.name

def format_annex(env, annex):
	if env.highlightedannex and env.highlightedannex == annex:
		return "\033[1m%s\033[0m" % annex.name
	else:
		return annex.name

def create_hosts_table(env, hosts, additional_data=True):
	""" builds a table """
	# we build a table: a 2 dimensional array
	table = []
	# the first line is the header
	table.append(["Host","Associated annexes"] if additional_data else ["Host"])
	# convert hosts to a list and sort the list
	hosts = list(hosts)
	hosts.sort(key=lambda h:str(h.name))
	for host in hosts:
		# create a row
		row = []
		# first column is the host name
		row.append(format_host(env,host))
		# second column (if wanted) are all associated annexes
		if additional_data:
			repos = host.repositories()
			row.append(", ".join(format_annex(env,repo.annex) for repo in sorted(repos,key=lambda r:r.annex.name)))
		# append row
		table.append(row)
	
	return hosts,table

def create_annexes_table(env, annexes, additional_data=True):
	""" builds a table """
	# we build a table: a 2 dimensional array
	table = []
	# the first line is the header
	table.append(["Annex","Associated hosts"] if additional_data else ["Annex"])
	# convert annexes to a list and sort the list
	annexes = list(annexes)
	annexes.sort(key=lambda a:str(a.name))
	for annex in annexes:
		# create a row
		row = []
		# first column is the annex name
		row.append(format_annex(env,annex))
		# second column (if wanted) are all associated hosts
		if additional_data:
			repos = annex.repositories()
			row.append(", ".join(format_host(env,repo.host) for repo in sorted(repos,key=lambda r:r.host.name)))
		# append row
		table.append(row)
	
	return annexes,table
		
def create_repositories_table(env, repositories):
	""" builds a table """
	# determine if additional columns have to be shown
	withspecial = any(repo.isSpecial() for repo in repositories)
	withdirect  = any(repo.direct for repo in repositories)
	withtrust   = any(repo.trust != "semitrust" for repo in repositories)
	withfiles   = any(repo.files for repo in repositories)
	withstrict  = any(repo.strict for repo in repositories)
	withdesc    = any(repo.hasNonTrivialDescription() for repo in repositories)
	
	# we build a table: a 2 dimensional array
	table = []
	
	# build table header
	header = ["Host","Annex","Path"]
	# additional columns:
	if withspecial: header.append("Special")
	if withdirect:  header.append("Direct")
	if withtrust:   header.append("Trust")
	if withfiles:   header.append("Files")
	if withstrict:  header.append("Strict")
	if withdesc:    header.append("Description")
	# the first line is the header
	table.append(header)
	
	# convert repositories to a list and sort the list
	repositories = list(repositories)
	repositories.sort(key=lambda r:str((r.host,r.annex,r.path)))
	for repo in repositories:
		# create a row
		row = []
		# first column is the host name
		row.append(format_host(env,repo.host))
		# second column is the annex name
		row.append(format_annex(env,repo.annex))
		# third column is the path
		row.append(repo.path if not repo.isSpecial() else "-")
		# further columns
		if withspecial:
			row.append("yes" if repo.isSpecial() else "")
		if withdirect:
			row.append("yes" if repo.direct else "")
		if withtrust:
			row.append(repo.trust if repo.trust != "semitrust" else "")
		if withstrict:
			row.append("yes" if repo.strict else "")
		if withfiles:
			row.append(repo.files if repo.files else "")
		if withdesc:
			row.append(repo.description if repo.hasNonTrivialDescription() else "")
		# append row
		table.append(row)

	return repositories,table

def create_connections_table(env, connections):
	""" builds a table """
	
	# determine if additional columns have to be shown
	withalwayson = any(conn.alwaysOn for conn in connections)
	
	# we build a table: a 2 dimensional array
	table = []

	# build table header
	header = ["Source","Destination","Path",]
	# additional columns:
	if withalwayson: header.append("Always on")
	# the first line is the header
	table.append(header)

	# convert connections to a list and sort the list
	connections = list(connections)
	connections.sort(key=lambda c:str((c.source,c.dest,c.path)))
	for conn in connections:
		# create a row
		row = []
		# first column is the source host name
		row.append(format_host(env,conn.source))
		# second column is the destination host name
		row.append(format_host(env,conn.dest))
		# third column is the path
		row.append(conn.path)
		# further columns
		if withalwayson:
			row.append("yes" if conn.alwaysOn else "")
		# append row
		table.append(row)
	return connections,table


#
# print 
#
def print_data(env, data_type, enumerated=False):
	""" print all data known for data type data_type """
	
	# get known objects
	objs = getattr(env.app,data_type).getAll()

	appendix = []

	# filter repositories if desired
	if data_type == "repositories":
		# filter host
		if env.host is not None:
			objs = [obj for obj in objs if obj.host == env.host]
			appendix.append("on host %s" % env.host.name)
			
		# filter annex
		if env.annex is not None:
			objs = [obj for obj in objs if obj.annex == env.annex]
			appendix.append("of annex %s" % env.annex.name)

	# filter connections if desired
	if data_type == "connections":
		# filter source
		if env.host is not None:
			objs = [obj for obj in objs if obj.source == env.host]
			appendix.append("from host %s" % env.host.name)
	
	# post process appendix
	appendix = " ".join(appendix)
	if appendix:
		appendix = " " + appendix
	
	if not objs:
		# state that there are not any objects of the given type
		print("There are no registered %s%s." % (data_type,appendix))
	else:
		# print the count
		print("There are %d registered %s%s:" % (len(objs),data_type,appendix))
		
		# create table
		objs,table = eval("create_%s_table"%data_type)(env,objs)

		# enumerate the lines if wanted
		if enumerated:
			table = enumerate_table(table)
		
		# print the table
		print_table(table)
	print()
	
	return objs


#
# actual functions
#
def show(env):
	# print known objs
	for data_type in ("hosts","annexes","repositories","connections"):
		print_data(env,data_type)

def edit(env):
	while True:
		# build ordered dict of options
		options = collections.OrderedDict()

		print()
		print_bold("Available options:",sep='')

		# edit commands
		data_types = ['hosts', 'annexes', 'repositories', 'connections']
		
		for data_type in data_types:
			# print option
			print("  edit [%s]%s list" % (data_type[0],data_type[1:]))
			
			# create edit command: break scoping rule
			def create_edit_command(data_type):
				return lambda: meta_edit_command(env,data_type)
			options[data_type[0]] = create_edit_command(data_type)
		
		# save command
		print("  [s]ave changes")
		def save():
			env.app.save()
			print_blue("saved")
		options["s"] = save
		
		# exit command
		print("  [e]xit")
		options["e"] = lambda: "exit"

		# let the user choose
		ret = choose(options)
		
		# if ret indicates 'exit', do it
		if ret == 'exit':
			break


def meta_edit_command(env, data_type):
	""" let the user edit the $obj list """
	print()
	print_blue("%s list editor started" % data_type)

	# small helper function
	def editor_helper(obj):
		print_blue("%s object editor started" % data_type)
		eval("edit_%s"%data_type)(env,obj)
		print_blue("%s object editor finished" % data_type)

		
	while True:
		print()
		
		# build ordered dict of options
		options = collections.OrderedDict()

		# print data in data_type, objs is a sorted version of the data
		objs = print_data(env, data_type, enumerated=True)
		
		# print available options
		print_bold("Available options:",sep='')
		
		# if objects exist, give the possiblity to edit them
		if objs:
			print("  edit [i]-th entry (i: 1-%d)"%len(objs))
			# create edit command: break scoping rule
			options[range(1,len(objs)+1)] = lambda ipp: editor_helper(objs[ipp-1])

		# create new ones
		print("  [c]reate a new entry")
		options["c"] = lambda: editor_helper(None)
		
		# save command
		print("  [s]ave changes")
		def save():
			env.app.save()
			print_blue("saved")
		options["s"] = save
		
		# back command
		print("  [b]ack")
		options["b"] = lambda: "back"

		# let the user choose
		ret = choose(options)
		
		# if ret indicates 'back', do it
		if ret == 'back':
			break

	print_blue("%s list editor finished" % data_type)

#
# data post processor
#
def valid_char_pp(valid_chars):
	""" checks that only valid characters are used """

	# convert valid_chars to a set
	valid_chars = set(valid_chars)

	# define post processor
	def postprocessor(s):
		assert set(s).issubset(valid_chars),\
				"invalid character detected: %s" % ",".join(set(s) - valid_chars)
		return s
	return postprocessor

	

def valid_values_pp(valid_values):
	""" select from the given values """
	# build identity mapping
	valid_values = {x:x for x in valid_values}
	# define post processor via fuzzy_match
	def postprocessor(s):
		""" checks that s is a valid value """
		return fuzzy_match.fuzzyMatch(s, valid_values)
	# return post processor
	return postprocessor

	

def sorted_obj_pp(env, data_type, sorted_objs):
	""" host/annex post processor """
	def postprocessor(s):
		# two modes: fuzzy match and number
		# first try if this is a number
		if s.isnumeric():
			# convert number
			n = int(s)-1
			# is it in the correct range?
			if 0 <= n < len(sorted_objs[data_type]):
				# we found something, return the name
				return sorted_objs[data_type][n].name
			else:
				print("%d is not a valid number as it is not in the right range" % (n+1))
		
		# otherwise, try to fuzzily match against a host name
		# this may raise an exception, this exception is used by ask_questions
		return getattr(env.app,data_type).fuzzyMatch(s).name
	return postprocessor


def repo_path_pp(s):
	""" the path has to be absolute or 'special' """
	if not s.startswith("/") and not s == "special":
		raise ValueError("path has to be absolute or 'special'")
	return s
		

def connection_path_pp(s):
	""" test has to be absolute or a ssh path """
	if not s.startswith("/") and not s.startswith("ssh://"):
		raise ValueError("invalid form")
	return s
		


#
# edit function
#
def edit_hosts(env, obj):
	""" edit hosts """

	to_create = not obj

	if to_create or env.unsafe:
		# we have to create a new object (or overwrite existing values)
		
		# gather questions
		questions = []
		
		# 1. name
		questions.append({"name":"name",
						"description":"host name",
						"default": None if to_create else obj.name,
						"postprocessor":valid_char_pp(structure_host.Host.VALID_CHARS)})
		
		# actually ask the questions
		answers = ask_questions(questions)
	
		# check if asking the questions was cancelled
		if answers is None:
			print("host creation cancelled.")
			return

		try:
			# pre process raw data
			name = answers["name"]

			if to_create:
				# create object
				obj = env.app.hosts.create(name)
			else:
				# overwrite (very unsafe)
				obj._name = name
		except Exception as e:
			print_red("an error occured:", e.args[0])
			return


	
def edit_annexes(env, obj):
	""" edit annexes """

	to_create = not obj

	if to_create or env.unsafe:
		# we have to create a new object (or overwrite existing values)
		
		# gather questions
		questions = []
		
		# 1. name
		questions.append({"name":"name",
						"description":"annex name",
						"default": None if to_create else obj.name,
						"postprocessor":valid_char_pp(structure_annex.Annex.VALID_CHARS)})
		
		# actually ask the questions
		answers = ask_questions(questions)
	
		# check if asking the questions was cancelled
		if answers is None:
			print("annex creation cancelled.")
			return


		try:
			# pre process raw data
			name = answers["name"]

			if to_create:
				# create object
				obj = env.app.annexes.create(name)
			else:
				# overwrite (very unsafe)
				obj._name = name
		except Exception as e:
			print_red("an error occured:", e.args[0])
			return

	else:
		print("Annex objects have are inmutable, edit request ignored")
	



def edit_repositories(env, obj):
	""" edit repositories """
	
	to_create = not obj

	if to_create or env.unsafe:
		# we have to create a new object (or overwrite existing values)
		
		# at least one host and one annex have to exist
		if not env.app.hosts.getAll() or not env.app.annexes.getAll():
			print("error: you have to have at least one host and one annex to be able to create a repository")
			return
		
		sorted_objs = {}
		
		# ask core data
		questions = []
		
		if env.host is None:
			# show host data
			sorted_objs["hosts"] = print_data(env, "hosts", enumerated=True)
			
			# 1. which host 
			questions.append({"name":"host",
								"description":"the host of the repository, use the first letters of the host name or a number from above",
								"default": None if to_create else obj.host.name,
								"postprocessor": sorted_obj_pp(env,"hosts",sorted_objs)})
		
		if env.annex is None:
			# show annex data
			sorted_objs["annexes"] = print_data(env, "annexes", enumerated=True)

			# 2. which annex
			questions.append({"name":"annex",
								"description":"the annex of the repository, use the first letters of the annex name or a number from above",
								"default": None if to_create else obj.annex.name,
								"postprocessor": sorted_obj_pp(env,"annexes",sorted_objs)})
		
		# 3. which path
		questions.append({"name":"path",
							"description":"absolute path to the repository or special for a special remote",
							"default": None if to_create else obj.path,
							"postprocessor": repo_path_pp})
		
		# 4. description
		questions.append({"name":"description",
							"description":"description of the repository, usually only needed when there are multiple repositories of the same annex on the same host",
							"default": None if to_create else obj._data.get("description"),
							"postprocessor": valid_char_pp(structure_repository.Repository.VALID_DESC_CHARS)})
		
		# actually ask the questions
		answers = ask_questions(questions)

		# check if asking the questions was cancelled
		if answers is None:
			print("repository creation cancelled.")
			return

		try:
			# pre process raw data
			host = env.app.hosts.fuzzyMatch(answers["host"]) if env.host is None else env.host
			annex = env.app.annexes.fuzzyMatch(answers["annex"])  if env.annex is None else env.annex
			path = answers["path"]
			description = answers["description"]

			if to_create:
				# create parameter
				data = {"description": description} if description else {}
				# create object
				obj = env.app.repositories.create(host,annex,path,**data)
			else:
				# overwrite (very unsafe)
				obj._host,obj._annex,obj._path = host,annex,path
				# overwrite description (or delete it)
				if description:
					obj._data["description"] = description
				elif "description" in obj._data:
					del obj._data["description"]
		except Exception as e:
			print_red("an error occured:", e.args[0])
			return
	
	print()
	print("editing the following repository:")
	print("host: ", obj.host.name)
	print("annex:", obj.annex.name)
	print("path: ", obj.path)
	
	# ask non core questions: direct, trust, files, strict
	# gather questions
	questions = []
	
	# 1. question: direct mode
	questions.append({"name":"direct",
						"description":"direct mode, valid values: true,false",
						"default":str(obj.direct).lower(),
						"postprocessor": valid_values_pp(("true","false"))})

	# 2. question: trust level
	trust_level = structure_repository.Repository.TRUST_LEVEL
	questions.append({"name":"trust",
						"description":"trust level, valid values: %s" % ",".join(trust_level),
						"default":obj.trust,
						"postprocessor": valid_values_pp(trust_level)})

	# 3. question: files expression
	questions.append({"name":"files",
						"description":"files expression which specifies the desired content of this repository",
						"default":obj.files if obj.files else "",
						"postprocessor": obj._sanitiseFilesExpression})

	# 4. question: strict?
	questions.append({"name":"strict",
						"description":"strict mode: only files which the files expression should be kept, valid values: true,false",
						"default":str(obj.strict).lower(),
						"postprocessor": valid_values_pp(("true","false"))})

	# actually ask the questions
	answers = ask_questions(questions)

	# check if asking the questions was cancelled
	if answers is None:
		print("repository property edit cancelled.")
		return
	
	# set values
	try:
		# parse values
		direct = (answers["direct"] == 'true')
		trust  = answers["trust"]
		files  = answers["files"]
		strict = (answers["strict"] == 'true')
		# set values
		obj.direct = direct
		obj.trust = trust
		obj.strict = strict
		obj.files = files # files should be last, as it more likely to fail
	except Exception as e:
		print_red("an error occured:", e.args[0])
		return


def edit_connections(env, obj):
	""" edit connections """

	to_create = not obj

	if to_create or env.unsafe:
		# we have to create a new object (or overwrite existing values)
		
		# at least two hosts have to exist
		if len(env.app.hosts.getAll()) < 2:
			print("error: you have to have at least two hosts to be able to create a connection")
			return
		
		sorted_objs = {}
		# show hosts and annexes
		for data_type in ("hosts",):
			sorted_objs[data_type] = print_data(env, data_type, enumerated=True)
		
		# ask core data
		questions = []

		if env.host is None:
			# 1. which source
			questions.append({"name":"source",
								"description":"the source of the connection, use the first letters of the host name or a number from above",
								"default": None if to_create else obj.source.name,
								"postprocessor": sorted_obj_pp(env,"hosts",sorted_objs)})

		# 2. which destination
		questions.append({"name":"destination",
							"description":"the destination of the connection, use the first letters of the host name or a number from above",
								"default": None if to_create else obj.dest.name,
							"postprocessor": sorted_obj_pp(env,"hosts",sorted_objs)})

		# 3. which path
		questions.append({"name": "path",
							"description": "form: mount: absolute path, ssh: ssh://<server>",
							"default": None if to_create else obj.path,
							"postprocessor": connection_path_pp})
		
		# actually ask the questions
		answers = ask_questions(questions)

		# check if asking the questions was cancelled
		if answers is None:
			print("connection creation cancelled.")
			return

		# create or overwrite object
		try:
			# pre process raw data
			source = env.app.hosts.fuzzyMatch(answers["source"]) if env.host is None else env.host
			destination = env.app.hosts.fuzzyMatch(answers["destination"])
			path = answers["path"]
			
			if to_create:
				# create object
				obj = env.app.connections.create(source,destination,path)
			else:
				# overwrite (very unsafe)
				obj._source,obj._dest,obj._path = source,destination,path
		except Exception as e:
			print_red("an error occured:", e.args[0])
			return
	
	print()
	print("editing the following connection:")
	print("source:     ", obj.source.name)
	print("destination:", obj.dest.name)
	print("path:       ", obj.path)
	
	# ask non core questions: direct, trust, files, strict
	# gather questions
	questions = []
	
	# 1. question: alwaysOn
	questions.append({"name":"alwayson",
						"description":"is the connection always available, valid values: true,false",
						"default":str(obj.alwaysOn).lower(),
						"postprocessor": valid_values_pp(("true","false"))})

	# actually ask the questions
	answers = ask_questions(questions)

	# check if asking the questions was cancelled
	if answers is None:
		print("connections property edit cancelled.")
		return
	
	# set values
	try:
		# parse values
		alwayson = (answers["alwayson"] == 'true')
		# set values
		obj.alwaysOn = alwayson
	except Exception as e:
		print_red("an error occured:", e.args[0])
		return
