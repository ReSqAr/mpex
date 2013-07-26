import collections

import structure_host
import structure_annex

#
# table helper functions
#
def print_table(table,sep=2):
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
		for column_length,item in zip(column_lengths,row):
			# print the item left justified
			print(item.ljust(column_length+sep),end='')
		# print a new line
		print()

		# the first line is the header
		if i == 0:
			print("-" * (sum(column_lengths) + (len(column_lengths)-1) * sep))

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
	# we build a table: a 2 dimensional array
	table = []
	# the first line is the header
	table.append(["Host","Annex","Path","Options"])
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
		row.append(repo.path)
		# fourth column are the options
		options = []
		if repo.direct:
			options.append("direct")
		if repo.strict:
			options.append("strict")
		if repo.files:
			options.append("files='%s'" % repo.files)
		if repo.trust != "semitrust":
			options.append("trust: %s" % repo.trust)
		if repo.hasNonTrivialDescription():
			options.append("description: %s" % repo.description)
		row.append(", ".join(options))
		# append row
		table.append(row)

	return repositories,table

def create_connections_table(connections):
	""" builds a table """
	# we build a table: a 2 dimensional array
	table = []
	# the first line is the header
	table.append(["Source","Destination","Path","Options"])
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
		# fourth column are the options
		options = []
		if conn.alwaysOn:
			options.append("always on")
		row.append(", ".join(options))
		# append row
		table.append(row)
	return connections,table


#
# ask questions
#
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

	while True:
		print()
		for question in questions:
			name = question["name"]
			
			# print the description
			print("%s: description: %s" % (name,question["description"]))
			# ask
			while True:
				inp = input("%s: new value [%s]: " % (name,answers[name]))
				
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
							print("%s: implicit change to: %s" % (name,inp))
					except Exception as e:
						# the post processor found an error
						print("%s: invalid input: %s" % (name,e.args[0]))
						continue
				
				# if we reach this point, everything is fine, we save the answer
				# and can proceed to the next question
				answers[name] = inp
				break
		
		print()
		# ask if everything is alright
		x = input("Are the above answers correct? Or cancel? [Y/n/c] ")
		
		if x.strip().lower().startswith("c"):
			# if the input starts with c, assume it is cancelled
			return None
		elif x.strip().lower().startswith("n"):
			# if the input starts with 'n', continue
			continue
		else:
			# default: we are done
			break
		
	# return the answers
	return answers


#
# actual functions
#
def show(app):
	# print known objs
	for obj_name in ("hosts","annexes","repositories","connections"):
		# print known objs
		objs = getattr(app,obj_name).getAll()
		if not objs:
			print("There are no registered %s." % obj_name)
		else:
			print("There are %d registered %s:" % (len(objs),obj_name))
			# create and print table
			_,table = eval("create_%s_table"%obj_name)(objs)
			print_table(table)
		print()


def edit(app):
	while True:
		print("Available options:")
		print("  edit [h]osts list")
		print("  edit [a]nnexes list")
		print("  edit [r]epositories list")
		print("  edit [c]onnections list")
		print("  [s]ave changes")
		print("  [e]xit")
		
		# ask the user what to do (until we have a valid answer)
		while True:
			key = input("Select [h,a,r,c,e]: ")
			if key not in ['h','a','r','c','e']:
				print("Invalid user input '%s'" % key)
				continue
			else:
				# we found something
				break
			
		if key == 'e':
			# exit
			break
		if key == 's':
			# save
			app.save()
		else:
			# edit command arguments
			edit_command_arguments = {'h':"hosts",
								'a':"annexes",
								'r':"repositories",
								'c':"connections",
							}
			# call function
			meta_edit_command(app,edit_command_arguments[key])

def meta_edit_command(app,obj_name):
	""" let the user edit the $obj list """
	print()
	print("\033[1;37;44m", "%s list editor" % obj_name, "\033[0m")
	while True:
		print()

		# print known objs
		objs = getattr(app,obj_name).getAll()
		if not objs:
			print("There are no registered %s." % obj_name)
		else:
			print("There are %d registered %s:" % (len(objs),obj_name))
			# create, enumerate and print table
			objs,table = eval("create_%s_table"%obj_name)(objs)
			table = enumerate_table(table)
			print_table(table)
		print()
		
		# print available options
		print("Available options:")
		if objs:
			print("  edit [i]-th entry (i: 1-%d)"%len(objs))
		print("  [c]reate a new entry")
		print("  [s]ave changes")
		print("  [b]ack")
	
		options = base_options = ["c","s","b"]
		if objs:
			options = ["i∊[1,%d]"%len(objs)] + options 

		# ask the user what to do (until we have a valid answer)
		while True:
			key = input("Select [%s]: " % ','.join(options))
			if key in base_options:
				# valid
				break
			else:
				# may be it is a number?
				try:
					# try to convert it to a number
					key = int(key) - 1
					# if it has the right range, select it
					if 0 <= key < len(objs):
						break
				except:
					pass
			# if we are here, the input was invalid
			print("Invalid user input '%s'" % key)
		
		print()
		
		if key == "b":
			# option 'back'
			break
		elif key == "s":
			# option 'save'
			app.save()
		else:
			# compute row to work on, or if the row should be created, None
			row = objs[key] if key != "c" else None
			# call edit command
			print("\033[1;37;44m", "%s object editor started" % obj_name, "\033[0m")
			eval("edit_%s"%obj_name)(app,row)
			print("\033[1;37;44m", "%s object editor finished" % obj_name, "\033[0m")




def edit_hosts(app,host):
	""" edit hosts """
	# a host cannot be edited
	if host is not None:
		print("Host objects have are inmutable, edit request ignored")
		return
	
	def postprocessor(name):
		""" test if creating an object with the name raises an error """
		return structure_host.Host(None,name).name
	questions = [{"name":"name", "description":"host name","postprocessor":postprocessor}]
	answers = ask_edit_questions(questions)
	
	# check if asking the questions was cancelled
	if answers is None:
		print("Host creation cancelled.")
		return
	
	# create the object
	try:
		app.hosts.create(answers["name"])
	except Exception as e:
		print("An error occured: %s" % e.args[0])
	
	
def edit_annexes(app,annex):
	""" edit annexes """
	# an annex cannot be edited
	if annex is not None:
		print("Annex objects have are inmutable, edit request ignored")
		return
	
	def postprocessor(name):
		""" test if creating an object with the name raises an error """
		return structure_annex.Annex(None,name).name
	questions = [{"name":"name", "description":"annex name","postprocessor":postprocessor}]
	answers = ask_edit_questions(questions)
	
	# check if asking the questions was cancelled
	if answers is None:
		print("Host creation cancelled.")
		return

	# create the object
	try:
		app.annexes.create(answers["name"])
	except Exception as e:
		print("An error occured: %s" % e.args[0])


def edit_repositories(app,obj):
	""" edit repositories """
	
	if not obj:
		# we have to create a new object
		
		# at least one host and one annex have to exist
		if not app.hosts.getAll() or not app.annexes.getAll():
			print("error: you have to have at least one host and one annex to be able to create a repository")
			return
		
		sorted_objs = {}
		# show hosts and annexes
		for obj_name in ("hosts","annexes",):
			# print known objs
			objs = getattr(app,obj_name).getAll()
			print("There are %d registered %s:" % (len(objs),obj_name))
			# create, enumerate and print table
			sorted_objs[obj_name],table = eval("create_%s_table"%obj_name)(objs,additional_data=False)
			table = enumerate_table(table)
			print_table(table)
			print()
		
		# ask core data
		questions = []
		# 1. which host 
		def postprocessor(s):
			# two modes: fuzzy match and number
			# first try if this is a number
			if s.isnumeric():
				# convert number
				n = int(s)-1
				# is it in the correct range?
				if 0 <= n < len(sorted_objs["hosts"]):
					# we found something, return the name
					return sorted_objs["hosts"][n].name
				else:
					print("%d is not a valid number as it is not in the right range" % (n+1))
			
			# otherwise, try to fuzzily match against a host name
			# this may raise an exception, this exception is used by ask_edit_questions
			return app.hosts.fuzzyMatch(s).name
			
		questions.append({"name":"host",
							"description":"the host of the repository, use the first letters of the host name or a number from above",
							"postprocessor": postprocessor})
		# 2. which annex
		def postprocessor(s):
			# two modes: fuzzy match and number
			# first try if this is a number
			if s.isnumeric():
				# convert number
				n = int(s)-1
				# is it in the correct range?
				if 0 <= n < len(sorted_objs["annexes"]):
					# we found something, return the name
					return sorted_objs["annexes"][n].name
				else:
					print("%d is not a valid number as it is not in the right range" % (n+1))
			
			# otherwise, try to fuzzily match against a annex name
			# this may raise an exception, this exception is used by ask_edit_questions
			return app.annexes.fuzzyMatch(s).name
			
		questions.append({"name":"annex",
							"description":"the annex of the repository, use the first letters of the annex name or a number from above",
							"postprocessor": postprocessor})
		# 3. which path
		def postprocessor(s):
			# test if this path is absolute
			if not s.startswith("/"):
				raise ValueError("path has to be absolute")
			return s
		
		questions.append({"name":"path",
							"description":"absolute path to the repository",
							"postprocessor": postprocessor})
		
		# actual ask the questions
		answers = ask_edit_questions(questions)

		# create the object
		try:
			# pre process raw data
			host = app.hosts.fuzzyMatch(answers["host"])
			annex = app.annexes.fuzzyMatch(answers["annex"])
			path = answers["path"]
			# create object
			obj = app.repositories.create(host,annex,path)
		except Exception as e:
			print("An error occured: %s" % e.args[0])
	
	# TODO: ask non core questions
	

def edit_connections(app,row):
	""" edit connections """
	raise NotImplementedError
