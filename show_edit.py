import collections
import readline
import textwrap

import lib.fuzzy_match

import structure_host
import structure_annex
import structure_repository


#
# table helper functions
#
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
		column_lengths = [max(len(row[i]),column_lengths[i]) for i in range(columns)]
	
	# output
	for i,row in enumerate(table):
		# print header in bold
		if i == 0: print("\033[1m",end="")

		for column_length,item in zip(column_lengths,row):
			# print the item left justified
			print(item.ljust(column_length+sep),end='')

		if i == 0: print("\033[0m",end="")

		# print a new line
		print()

		# the first line is the header
		if i == 0:
			print(header_sep * (sum(column_lengths) + (len(column_lengths)-1) * sep))

def enumerate_table(table):
	""" adds the row number to the first line """
	return [ [str(i-1+1) if i>0 else "n"] + row for i,row in enumerate(table) ]

def create_hosts_table(hosts,additional_data=True):
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
		row.append(host.name)
		# second column (if wanted) are all associated annexes
		if additional_data:
			repos = host.repositories()
			row.append(", ".join(sorted(repo.annex.name for repo in repos)))
		# append row
		table.append(row)
	
	return hosts,table

def create_annexes_table(annexes,additional_data=True):
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
		row.append(annex.name)
		# second column (if wanted) are all associated hosts
		if additional_data:
			repos = annex.repositories()
			row.append(", ".join(sorted(repo.host.name for repo in repos)))
		# append row
		table.append(row)
	
	return annexes,table
		
def create_repositories_table(repositories):
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
		row.append(repo.host.name)
		# second column is the annex name
		row.append(repo.annex.name)
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

def create_connections_table(connections):
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
		row.append(conn.source.name)
		# second column is the destination host name
		row.append(conn.dest.name)
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
		objs,table = eval("create_%s_table"%data_type)(objs)

		# enumerate the lines if wanted
		if enumerated:
			table = enumerate_table(table)
		
		# print the table
		print_table(table)
	print()
	
	return objs


#
# ask questions
#
def choose(options):
	"""
		choose one of the options:
		options: dictionary: letter/possible range -> function
	"""
	# ask the user what to do (until we have a valid answer)
	while True:
		# build a nice representation of all options
		def convert(option):
			if isinstance(option,range):
				assert option.step == 1, "step is wrong"
				return "i∊[%d,%d]" % (option.start,option.stop-1)
			else:
				return str(option)
		opt_text = ",".join(convert(opt) for opt in options.keys())
		
		# ask question
		answer = input("\033[1mSelect [%s]:\033[0m " % opt_text)
		
		# find selected option
		selected = options.get(answer)
		
		# if we found a selected option, call it
		if selected:
			print()
			return selected()
		
		# otherwise we have a special option
		for option,f in options.items():
			# special options are: range

			# try to interpret answer as a number in the given range
			if isinstance(option,range):
				try:
					# convert to an integer
					number = int(answer)
				except:
					# if it fails, it cannot be a number
					continue
				
				# if it has the right range, select it
				if number in option:
					print()
					return f(number)
		
		# if we are here, the input was invalid
		print("Invalid user input '%s'" % answer)

		

def ask_edit_questions(questions):
	"""
		ask the user the given questions,
		questions is a list of dictionaries with keys:
			name, description, [default], [postprocessor]
		postprocessor may raise an error if the input is invalid
	"""
	answers = collections.OrderedDict()
	
	# set default value in answers:
	for question in questions:
		name = question["name"]
		# set
		answers[name] = question.get("default") if question.get("default") else ""

	prefixlength = max(len(question["name"]) for question in questions) + 1

	while True:
		print()
		for question in questions:
			name = question["name"]
			
			
			# print the description (wrapped)
			for i,line in enumerate(textwrap.wrap(question["description"],70)):
				if i == 0:
					print("\033[1m%s:\033[0m"%name," " * (prefixlength - len(name)-1),end="")
				else:
					print(" " * (prefixlength+1),end="")
				print(line)
			
			# ask
			while True:
				inp = input("%s \033[1mnew value [%s]:\033[0m " % (" "*prefixlength,answers[name]))
				
				# if the input is empty, use the default value
				if not inp:
					inp = answers[name]
				
				# strip input, this means you can set '' via entering a space
				inp = inp.strip()
				
				# post process data
				postprocessor = question.get("postprocessor")
				if postprocessor:
					try:
						# apply the postprocessor
						orig,inp = inp,postprocessor(inp)
						# if the original version differs from the post processed one,
						# show it
						if orig != inp:
							print(" "*prefixlength, "implicit change to: %s" % (inp,))
					except Exception as e:
						# the post processor found an error
						print(" "*prefixlength, "invalid input: %s" % (e.args[0],))
						continue
				
				# if we reach this point, everything is fine, we save the answer
				# and can proceed to the next question
				answers[name] = inp
				break
		
		print()
		# ask if everything is alright
		x = input("\033[1mAre the above answers correct? Or cancel? [Y/n/c]\033[0m ")
		
		if x.strip().lower().startswith("c"):
			# if the input starts with c, assume it is cancelled
			return None
		elif x.strip().lower().startswith("n"):
			# if the input starts with 'n', continue
			continue
		else:
			# default: we are done
			break
	print()
	
	# return the answers
	return answers



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
		print("\033[1mAvailable options:\033[0m")

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
			print("\033[1;37;44m", "saved", "\033[0m")
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
	print("\033[1;37;44m", "%s list editor started" % data_type, "\033[0m")

	# small helper function
	def editor_helper(obj):
		print("\033[1;37;44m", "%s object editor started" % data_type, "\033[0m")
		eval("edit_%s"%data_type)(env,obj)
		print("\033[1;37;44m", "%s object editor finished" % data_type, "\033[0m")

		
	while True:
		print()
		
		# build ordered dict of options
		options = collections.OrderedDict()

		# print data in data_type, objs is a sorted version of the data
		objs = print_data(env, data_type, enumerated=True)
		
		# print available options
		print("\033[1mAvailable options:\033[0m")
		
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
			print("\033[1;37;44m", "saved", "\033[0m")
		options["s"] = save
		
		# back command
		print("  [b]ack")
		options["b"] = lambda: "back"

		# let the user choose
		ret = choose(options)
		
		# if ret indicates 'back', do it
		if ret == 'back':
			break

	print("\033[1;37;44m", "%s list editor finished" % data_type, "\033[0m")

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
	# define post processor via lib.fuzzy_match
	def postprocessor(s):
		""" checks that s is a valid value """
		return lib.fuzzy_match.fuzzyMatch(s, valid_values)
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
		# this may raise an exception, this exception is used by ask_edit_questions
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
		answers = ask_edit_questions(questions)
	
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
			print("\033[1;37;41m", "an error occured: %s" % e.args[0], "\033[0m")
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
		answers = ask_edit_questions(questions)
	
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
			print("\033[1;37;41m", "an error occured: %s" % e.args[0], "\033[0m")
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
		answers = ask_edit_questions(questions)

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
			print("\033[1;37;41m", "an error occured: %s" % e.args[0], "\033[0m")
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
	answers = ask_edit_questions(questions)

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
		print("\033[1;37;41m", "an error occured: %s" % e.args[0], "\033[0m")
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
		answers = ask_edit_questions(questions)

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
			print("\033[1;37;41m", "an error occured: %s" % e.args[0], "\033[0m")
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
	answers = ask_edit_questions(questions)

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
		print("\033[1;37;41m", "an error occured: %s" % e.args[0], "\033[0m")
		return
