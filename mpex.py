#!/usr/bin/env python3

import os
import argparse
import sys
import textwrap
import time

import lib.fuzzy_match

import application
import show_edit

CONFIG_PATH = "~/.config/mpex/"
CONFIG_PATH = os.path.expanduser(CONFIG_PATH)


def parse_annex_names(app,args):
	""" parse annexes supplied by the user """
	# if nothing is given, return all
	if not args.annex:
		return app.annexes.getAll()
	
	# save
	annex_names = args.annex 
	
	# find all known names
	known_annexes = {annex.name: annex for annex in app.annexes.getAll()}

	selected_annexes = set()

	for annex_name in annex_names:
		# find annexes
		annexes = set(lib.fuzzy_match.fuzzyMultiMatch(annex_name,known_annexes))
		if not annexes:
			print("WARNING: could not parse the annex '%s'" % annex_name)
			sys.exit(1)
		# add found annexes
		selected_annexes |= annexes
	
	return selected_annexes

#
# parser used by the next function
#
apply_parser = argparse.ArgumentParser(add_help=False)
apply_parser.add_argument('--remote', action="store_true",
						help="execute the command also on all connected remotes")
apply_parser.add_argument('--remoteonly', action="store_true",
						help="execute the command only on connected remotes")
apply_parser.add_argument('--hops', type=int, default=2,
						help="when remote is given, the maximal number of hops")
apply_parser.add_argument('--simulate', action="store_true",
						help="only simulate the commands")
apply_parser.add_argument('--verbose', type=int,
						default=application.Application.VERBOSE_NORMAL,
						help="verbosity level: 0 [1] 2")


def apply_function(args,f):
	""" apply f to all given annex_names """
	# create application
	app = application.Application(CONFIG_PATH, verbose=args.verbose, simulate=args.simulate)

	# parse annex names
	selected_annexes = parse_annex_names(app,args)
	
	# give the user the chance to understand what the program is doing
	names = ", ".join(sorted(annex.name for annex in selected_annexes))
	if args.verbose <= app.VERBOSE_IMPORTANT:
		print()
		print("selected annexes: %s" % names)
		print()
		time.sleep(0.5)
	
	# sort order for repositories
	r_key = lambda r: str((r.annex,r.path))
	
	# sort out execution targets
	if args.remoteonly:
		# only remote
		localExecution,remoteExecution = False,True
	elif args.remote:
		# both
		localExecution,remoteExecution = True,True
	else:
		# default: only local
		localExecution,remoteExecution = True,False
	
	
	# if remoted execution is wanted and we are still close enough to the origin
	if remoteExecution and args.hops > 0:
		for connection in app.getConnections():
			if not connection.isOnline():
				print("Connection to %s is not online." % connection.dest.name)
				continue
			
			if connection.isLocal():
				# if the repositories are locally accessible:
				for repo in sorted(app.getConnectedRepositories(connection),key=r_key):
					# check if the repo belongs to a selected annex
					# and that it is not special, if both conditions
					# are true, execute f
					if repo.annex in selected_annexes and not repo.isSpecial():
						f(repo)
			elif connection.supportsRemoteExecution():
				# if the connection allows remote execution, first compute the remote command
				# start with the current command
				cmd = sys.argv[:]
				# adjust hops
				for i,piece in enumerate(cmd):
					if piece == "--hops":
						# format: --hops n, new command line: --hops (n-1)
						cmd[i+1] = str(args.hops-1)
						break
					elif piece.startswith("--hops="):
						# format: --hops=n, new command line: --hops=(n-1)
						cmd[i] = "--hops=%s" % (args.hops-1)
						break
				else:
					# no hops argument in the original command given: just add it
					cmd = cmd[:2] + ["--hops",str(args.hops-1)] + cmd[2:]

				# execute the command on the target machine
				connection.executeRemotely(cmd)
			else:
				raise ValueError("Connection %s does not permit remote exection."%connection)
	
	# if the command should be executed locally
	if localExecution:
		for repo in sorted(app.getHostedRepositories(),key=r_key):
			# check if the repo belongs to a selected annex, if yes, then execute f
			if repo.annex in selected_annexes and not repo.isSpecial():
				f(repo)
	

#
# initialise repositories
#
def init_init(parsers):
	parser = parsers.add_parser('init', help='create repositories',parents=[apply_parser])
	parser.add_argument('annex', nargs='*', help="Annex names")
	parser.add_argument('--ignorenonempty', action='store_true', default=False,
							help="initialise directories even if they are non empty")
	parser.set_defaults(func=func_init)

def func_init(args):
	def repo_init(repo):
		repo.init(ignorenonempty=args.ignorenonempty)
	apply_function(args,repo_init)
	
#
# reinitialise repositories
#
def init_reinit(parsers):
	parser = parsers.add_parser('reinit', help='reinitialise repositories',parents=[apply_parser])
	parser.add_argument('annex', nargs='*', help="annex names")
	parser.set_defaults(func=func_reinit)

def func_reinit(args):
	def repo_reinit(repo):
		repo.setProperties()
	apply_function(args,repo_reinit)
	
#
# finalise repositories
#
def init_finalise(parsers):
	parser = parsers.add_parser('finalise', help='finalise repositories',parents=[apply_parser])
	parser.add_argument('annex', nargs='*', help="annex names")
	parser.set_defaults(func=func_finalise)

def func_finalise(args):
	def repo_finalise(repo):
		repo.finalise()
	apply_function(args,repo_finalise)
	
#
# synchronise repositories
#
def init_sync(parsers):
	parser = parsers.add_parser('sync', help='synchronise repositories',parents=[apply_parser])
	parser.add_argument('annex', nargs='*', help="annex names")
	parser.set_defaults(func=func_sync)

def func_sync(args):
	def repo_sync(repo):
		repo.sync()
	apply_function(args,repo_sync)
	

#
# copy repositories
#
def init_copy(parsers):
	parser = parsers.add_parser('copy', help='copy repositories',parents=[apply_parser])
	parser.add_argument('annex', nargs='*', help="annex names")
	parser.add_argument('--files', default=None, help="files expression for the local host")
	parser.add_argument('--strict', action="store_true", help="apply strict")
	parser.add_argument('--nostrict', action="store_true", help="apply no strict")
	parser.set_defaults(func=func_copy)

def func_copy(args):
	# get strict flag
	strict = None
	if args.strict:
		strict = True
	if args.nostrict:
		strict = False
	
	def repo_copy(repo):
		repo.copy(files=args.files,strict=strict)
	apply_function(args,repo_copy)

#
# run the given command against the repositories
#
def init_command(parsers):
	epilog  = textwrap.dedent("""\
				Examples:
				   %(prog)s git status
				   %(prog)s -- git annex status --fast
				   %(prog)s cat .git/config
				""")
	parser = parsers.add_parser('command',
									help='run the given command against the repositories',
									epilog=epilog,
									formatter_class=argparse.RawDescriptionHelpFormatter,
									parents=[apply_parser])
	#parser.add_argument('annex', nargs='*', help="Annex names")
	parser.add_argument('command', nargs='+', help="command to run")
	parser.set_defaults(func=func_command)

def func_command(args):
	# select all annexes
	args.annex = None
	
	def repo_command(repo):
		# change path
		repo.changePath()
		if repo.app.verbose <= repo.app.VERBOSE_IMPORTANT:
			print("\033[1;37;44m running the command for %s in %s \033[0m" % (repo.annex.name,repo.path))
		# run the command in the directory
		repo.executeCommand(args.command)
		if repo.app.verbose <= repo.app.VERBOSE_IMPORTANT:
			print()
	apply_function(args,repo_command)


#
#
# show data
#
def init_show(parsers):
	parser = parsers.add_parser('show', help='show data')
	parser.set_defaults(func=func_show)

def func_show(args):
	# create application
	app = application.Application(CONFIG_PATH)
	
	# show app data
	show_edit.show(app)

#
# edit data
#
def init_edit(parsers):
	parser = parsers.add_parser('edit', help='edit data')
	parser.set_defaults(func=func_edit)

def func_edit(args):
	# create application
	app = application.Application(CONFIG_PATH)

	try:
		# edit app data
		show_edit.edit(app)
	except KeyboardInterrupt:
		print()
		print("interrupted, going down WITHOUT saving")
		return

#
# set host
#
def init_sethost(parsers):
	parser = parsers.add_parser('sethost', help='set the current host')
	parser.add_argument('host', help="host name")
	parser.set_defaults(func=func_sethost)

def func_sethost(args):
	# create application
	app = application.Application(CONFIG_PATH)

	try:
		host = app.hosts.fuzzyMatch(args.host)
		print("setting host to %s." % host.name)
		app.setCurrentHost(host)
	except Exception as e:
		print("an error has occured: %s" % e.args[0])


#
# migrate
#
def init_migrate(parsers):
	epilog  = "This command is potentially dangerous as it deletes all remotes from .git/config"\
	          " via running 'git remote remove $remote' for all remotes. This command"\
	          " also implicitly removes all remote-tracking branches. Afterwards, mpex"\
	          " adds all remotes known to it. It is not dangerous for your data"\
	          " however git may or may not be able to reestablish the logical" \
	          " dependances of the commits, that is your history. So please make sure"\
	          " that you synchronised all your repositories before running this command."
	parser = parsers.add_parser('migrate',
									help='migrate repositories',
									epilog=epilog,
									parents=[apply_parser])
	parser.add_argument('annex', nargs='*', help="annex names")
	parser.set_defaults(func=func_migrate)

def func_migrate(args):
	
	print("This command is potentially DANGEROUS. Have you read the help and understood the consequences?")
	x = input("If yes, type YES: ")
	
	if x.strip() != "YES":
		print("leaving")
		return
	
	def repo_migrate(repo):
		repo.deleteAllRemotes()
		repo.setProperties()
	apply_function(args,repo_migrate)



#
# create and run parser
#
def runParser():
	# create the top-level parser
	parser = argparse.ArgumentParser(prog='mpex')


	# create sub parsers
	subparsers = parser.add_subparsers()
	init_init(subparsers)
	init_reinit(subparsers)
	init_finalise(subparsers)
	init_sync(subparsers)
	init_copy(subparsers)
	init_command(subparsers)
	init_show(subparsers)
	init_edit(subparsers)
	init_sethost(subparsers)
	init_migrate(subparsers)

	# parse arguments and call function
	args = parser.parse_args()
	
	if hasattr(args,"func"):
		# if everything is OK, call the function
		try:
			args.func(args)
		except (KeyboardInterrupt,application.InterruptedException):
			print()
			print("interrupted")
			return

	else:
		# print a warning
		parser.print_usage()
		print("Error: too few arguments")
	