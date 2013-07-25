

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

def create_hosts_table(hosts):
	""" builds a table """
	# we build a table: a 2 dimensional array
	table = []
	# the first line is the header
	table.append(["Host","Associated annexes"])
	# convert hosts to a list and sort the list
	hosts = list(hosts)
	hosts.sort(key=lambda h:str(h.name))
	for host in hosts:
		# create a row
		row = []
		# first column is the host name
		row.append(host.name)
		# second column are all associated annexes
		repos = host.repositories()
		row.append(", ".join(sorted(repo.annex.name for repo in repos)))
		# append row
		table.append(row)
	
	return hosts,table

def create_annexes_table(annexes):
	""" builds a table """
	# we build a table: a 2 dimensional array
	table = []
	# the first line is the header
	table.append(["Annex","Associated hosts"])
	# convert annexes to a list and sort the list
	annexes = list(annexes)
	annexes.sort(key=lambda a:str(a.name))
	for annex in annexes:
		# create a row
		row = []
		# first column is the annex name
		row.append(annex.name)
		# second column are all associated hosts
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
				name, description, [default], [errors]
	"""
	answers = {}
	
	while True:
		print()
		for question in questions:
			name = question["name"]
			
			# set default value in answers:
			if name not in answers:
				answers[name] = question.get("default")
				if answers[name] is None:
					answers[name] = ""
			
			# print the description
			print("%s: description: %s" % (name,question["description"]))
			# ask
			while True:
				x = input("%s: new value [%s]: " % (name,answers[name]))
				
				# if the input is empty, use the default value
				if not x:
					x = answers[name]
				
				# strip input
				x = x.strip()
				
				# check if the input is valid
				errors = question.get("errors")
				if errors:
					output = errors(x)
					if output is not None:
						# the error checker found an error
						print("%s: invalid input: %s" % (name,output))
						continue
				
				# if we reach this point, everything is fine, we save the answer
				# and can proceed # to the next question
				answers[name] = x
				break
		
		print()
		# ask if everything is alright
		x = input("Are the above answers correct? [Y/n] ")
		# only reask all questions if the user's answer starts with 'n'
		if not x.strip().lower().startswith("n"):
			break
	
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
			# create, enumerate and print table
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
			eval("edit_%s"%obj_name)(app,row)




def edit_hosts(app,host):
	""" edit hosts """
	# a host cannot be edited
	if host is not None:
		print("Host objects have are inmutable, edit request ignored")
		return
	
	questions = [{"name":"name", "description":"host name",
					"errors":lambda s: None if s else "host name has to be non-empty"}]
	answers = ask_edit_questions(questions)
	
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
	
	questions = [{"name":"name", "description":"annex name",
					"errors":lambda s: None if s else "annex name has to be non-empty"}]
	answers = ask_edit_questions(questions)
	
	try:
		app.annexes.create(answers["name"])
	except Exception as e:
		print("An error occured: %s" % e.args[0])


def edit_repositories(app,row):
	""" edit repositories """
	raise NotImplementedError


def edit_connections(app,row):
	""" edit connections """
	raise NotImplementedError
