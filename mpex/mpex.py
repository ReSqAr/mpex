import os
import argparse
import sys
import textwrap
import time
import xdg

from .lib import fuzzy_match
from .lib.terminal import print_blue, print_red, print_green

from . import application
from . import show_edit

from . import grouped_repositories

CONFIG_PATH = xdg.XDG_CONFIG_HOME
if not CONFIG_PATH:
    CONFIG_PATH = os.path.expanduser('~/.config')
CONFIG_PATH = os.path.join(CONFIG_PATH, 'mpex')


def parse_annex_names(app, args):
    """ parse annexes supplied by the user """
    # if nothing is given, return all
    if not args.annex:
        return app.annexes.get_all()

    # save
    annex_names = args.annex

    # find all known names
    known_annexes = {annex.name: annex for annex in app.annexes.get_all()}

    selected_annexes = set()

    for annex_name in annex_names:
        # find annexes
        annexes = set(fuzzy_match.fuzzy_multi_match(annex_name, known_annexes))
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
apply_parser.add_argument('--hosts', default=None,
                          help="comma seperated list of hosts on which the command should be executed")
apply_parser.add_argument('--remotempex', default="mpex", metavar="cmd",
                          help="remote mpex command (default: mpex)")
apply_parser.add_argument('--hops', type=int, default=2,
                          help="when remote is given, the maximal number of hops")
apply_parser.add_argument('--simulate', action="store_true",
                          help="only simulate the commands")
apply_parser.add_argument('--verbose', type=int,
                          default=application.Application.VERBOSE_NORMAL,
                          help="verbosity level: 0 [1] 2")


def apply_function(args, f):
    """ apply f to all given annex_names """
    # create application
    app = application.Application(CONFIG_PATH, verbose=args.verbose, simulate=args.simulate)

    # parse annex names
    selected_annexes = parse_annex_names(app, args)

    # give the user the chance to understand what the program is doing
    names = ", ".join(sorted(annex.name for annex in selected_annexes))
    if args.verbose <= app.VERBOSE_IMPORTANT:
        print()
        print("selected annexes: %s" % names)
        print()
        time.sleep(0.5)

    # sort order for repositories
    r_key = lambda r: str((r.annex, r.path))

    # select execution targets
    hosts_filter = None
    if args.hosts is not None:
        # split the comma separated list
        hosts = [host.strip() for host in args.hosts.split(",")]

        # find all known names
        known_hosts = {host.name: host for host in app.hosts.get_all()}
        hosts_filter = set()
        for host_name in hosts:
            # find annexes
            selected_hosts = set(fuzzy_match.fuzzy_multi_match(host_name, known_hosts))
            if not selected_hosts:
                print("WARNING: could not parse the host '%s'" % host_name)
                sys.exit(1)
            # add found hosts
            hosts_filter |= selected_hosts

        # only execute locally, if the current host is specified
        if app.current_host() in hosts_filter:
            local_execution = True
            # remove local host
            hosts_filter.remove(app.current_host())
        else:
            local_execution = False

        # only execute remotely, if the filter is non-empty
        remote_execution = bool(hosts_filter)

    elif args.remoteonly:
        # only remote
        local_execution, remote_execution = False, True
    elif args.remote:
        # both
        local_execution, remote_execution = True, True
    else:
        # default: only local
        local_execution, remote_execution = True, False

    # list of connections
    connections = []

    # if remote execution is requested and we are still close enough to the origin
    if remote_execution and args.hops > 0:
        for connection in app.get_connections():
            # filter hosts if the host filter is active
            if hosts_filter is not None and connection.dest not in hosts_filter:
                continue
            # if the connection is available, use it
            if connection.is_online():
                connections.append(connection)

        # sort connections, non-local connections first
        connections.sort(key=lambda c: c.is_local())

        # state the connected hosts

        if connections:
            print("found connections to the following hosts:", ", ".join(sorted(c.dest.name for c in connections)))
        else:
            print("found no connections to other hosts")

    # if local execution is requested, add the trivial connection
    if local_execution:
        connections.append(None)

    # actually execute f
    for connection in connections:
        if connection is None or connection.is_local():
            # if the repositories are locally accessible
            if connection is None:
                # if we have the trivial connection, use the locally hosted repositories
                repositories = app.get_hosted_repositories()
            else:
                # otherwise, all repositories which can be accessed via the connection
                repositories = app.get_connected_repositories(connection)

            # iterate over all found repositories
            for repo in sorted(repositories, key=r_key):
                # check if the repo belongs to a selected annex
                # and that it is not special, if both conditions
                # are true, execute f
                if repo.annex in selected_annexes and not repo.is_special():
                    f(repo)

        elif connection.supports_remote_execution():
            # if the connection allows remote execution, first compute the remote command
            # based on the current command
            cmd = sys.argv[:]

            # adjust command name
            cmd[0] = args.remotempex

            # adjust hops
            for i, piece in enumerate(cmd):
                if piece == "--hops":
                    # format: --hops n, new command line: --hops (n-1)
                    cmd[i + 1] = str(args.hops - 1)
                    break
                elif piece.startswith("--hops="):
                    # format: --hops=n, new command line: --hops=(n-1)
                    cmd[i] = "--hops=%s" % (args.hops - 1)
                    break
            else:
                # no hops argument in the original command given: just add it
                cmd = cmd[:2] + ["--hops", str(args.hops - 1)] + cmd[2:]

            # execute the command on the target machine
            print()
            print_green("executing command on host %s" % connection.dest.name)
            connection.execute_remotely(cmd, ignore_exception=True, print_ignored_exception=True)
            print_green("command finished on host %s" % connection.dest.name)
            print()
        else:
            raise ValueError("Connection %s does not permit remote execution." % connection)


#
# initialise repositories
#
def init_init(parsers):
    parser = parsers.add_parser('init', help='create repositories', parents=[apply_parser])
    parser.add_argument('annex', nargs='*', help="Annex names")
    parser.add_argument('--ignorenonempty', action='store_true', default=False,
                        help="initialise directories even if they are non empty")
    parser.set_defaults(func=func_init)


def func_init(args):
    def repo_init(repo):
        repo.init(ignore_nonempty=args.ignorenonempty)

    apply_function(args, repo_init)


#
# reinitialise repositories
#
def init_reinit(parsers):
    parser = parsers.add_parser('reinit', help='reinitialise repositories', parents=[apply_parser])
    parser.add_argument('annex', nargs='*', help="annex names")
    parser.set_defaults(func=func_reinit)


def func_reinit(args):
    def repo_reinit(repo):
        repo.set_properties()

    apply_function(args, repo_reinit)


#
# finalise repositories
#
def init_finalise(parsers):
    parser = parsers.add_parser('finalise', help='finalise repositories', parents=[apply_parser])
    parser.add_argument('annex', nargs='*', help="annex names")
    parser.set_defaults(func=func_finalise)


def func_finalise(args):
    def repo_finalise(repo):
        repo.finalise()

    apply_function(args, repo_finalise)


#
# synchronise repositories
#
def init_sync(parsers):
    parser = parsers.add_parser('sync', help='synchronise repositories', parents=[apply_parser])
    parser.add_argument('annex', nargs='*', help="annex names")
    parser.set_defaults(func=func_sync)


def func_sync(args):
    def repo_sync(repo):
        repo.sync()

    apply_function(args, repo_sync)


#
# copy repositories
#
def init_copy(parsers):
    parser = parsers.add_parser('copy', help='copy repositories', parents=[apply_parser])
    parser.add_argument('annex', nargs='*', help="annex names")
    parser.add_argument('--all', action="store_true", help="call git-annex with --all")
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
        repo.copy(copy_all=args.all, files=args.files, strict=strict)

    apply_function(args, repo_copy)


#
# group repositories
#
def init_group(parsers):
    parser = parsers.add_parser('group', help='group repositories', parents=[apply_parser])
    parser.add_argument('annex', nargs='*', help="annex names")
    parser.add_argument('--lines', type=int, default=5,
                        help="number of printed lines per repository (default: 5)")
    parser.add_argument('--no-untrusted', action="store_true",
                        help="only show trusted repositories")
    parser.set_defaults(func=func_group)


def func_group(args):
    def repo_group(repo):
        if repo.app.verbose <= repo.app.VERBOSE_IMPORTANT:
            print_blue("grouping repositories of", repo.annex.name, "in", repo.path)
            print()

        grouped_repositories.do_report(repo.local_path, args.lines, args.no_untrusted)
        print()

    apply_function(args, repo_group)


#
# run the given command against the repositories
#
def init_command(parsers):
    epilog = textwrap.dedent("""\
                Examples:
                   %(prog)s git status
                   %(prog)s -- git annex status --fast
                   %(prog)s cat .git/config
                """)
    parser = parsers.add_parser('command',
                                help='run the given command against the selected repositories',
                                epilog=epilog,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                parents=[apply_parser])
    # parser.add_argument('annex', nargs='*', help="Annex names")
    parser.add_argument('--force', action="store_true", help="ignore exceptions")
    parser.add_argument('command', nargs='+', help="command to run")
    parser.set_defaults(func=func_command)


def func_command(args):
    # select all annexes
    args.annex = None

    def repo_command(repo):
        # change path
        repo.change_path()
        if repo.app.verbose <= repo.app.VERBOSE_IMPORTANT:
            print_blue("running the command for", repo.annex.name, "in", repo.local_path)
        # run the command in the directory
        repo.execute_command(args.command, ignore_exception=args.force)
        if repo.app.verbose <= repo.app.VERBOSE_IMPORTANT:
            print()

    apply_function(args, repo_command)


#
# show/edit helper
#

# parser used by the next function
show_edit_parser = argparse.ArgumentParser(add_help=False)
show_edit_parser.add_argument('--host', default=None,
                              help="restrict show/edit to the given host")
show_edit_parser.add_argument('--annex', default=None,
                              help="restrict show/edit to the given annex")


def create_env(args):
    # create application
    app = application.Application(CONFIG_PATH)

    # define environment
    class Env:
        def __init__(self):
            self.app = app
            self.host = app.hosts.fuzzy_match(args.host) if args.host is not None else None
            self.annex = app.annexes.fuzzy_match(args.annex) if args.annex is not None else None

            # find the host which should be highlighted
            if self.host:
                self.highlighted_host = self.host
            else:
                try:
                    self.highlighted_host = app.current_host()
                except:
                    # there is no distinguished host
                    self.highlighted_host = None

            # find annex which should be highlighted
            self.highlighted_annex = self.annex

    # create environment
    return Env()


#
# show data
#
def init_show(parsers):
    parser = parsers.add_parser('show', help='show data', parents=[show_edit_parser])
    parser.set_defaults(func=func_show)


def func_show(args):
    # create env
    env = create_env(args)

    # show app data
    show_edit.show(env)


#
# edit data
#
def init_edit(parsers):
    parser = parsers.add_parser('edit', help='edit data', parents=[show_edit_parser])
    parser.add_argument('--unsafe', action="store_true",
                        help="allow unsafe operations (default: off)")

    parser.set_defaults(func=func_edit)


def func_edit(args):
    # create env
    env = create_env(args)

    # parse unsafe
    env.unsafe = args.unsafe

    if env.unsafe:
        print_red("WARNING: take extreme care as UNSAFE operations are allowed")

    try:
        # edit app data
        show_edit.edit(env)
    except KeyboardInterrupt:
        print()
        print("interrupted, going down WITHOUT saving")
        return


#
# set host
#
def init_set_host(parsers):
    parser = parsers.add_parser('sethost', help='set the current host')
    parser.add_argument('host', help="host name")
    parser.set_defaults(func=func_set_host)


def func_set_host(args):
    # create application
    app = application.Application(CONFIG_PATH)

    try:
        host = app.hosts.fuzzy_match(args.host)
        print("setting host to %s." % host.name)
        app.set_current_host(host)
    except Exception as e:
        print("an error has occurred: %s" % e.args[0])


#
# migrate
#
def init_migrate(parsers):
    epilog = "This command is potentially dangerous as it deletes all remotes from .git/config" \
             " via running 'git remote remove $remote' for all remotes. This command" \
             " also implicitly removes all remote-tracking branches. Afterwards, mpex" \
             " adds all remotes known to it. It is not dangerous for your data" \
             " however git may or may not be able to reestablish the logical" \
             " dependencies of the commits, that is your history. So please make sure" \
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
        repo.delete_all_remotes()
        repo.set_properties()

    apply_function(args, repo_migrate)


#
# create and run parser
#
def run_parser():
    # create the top-level parser
    parser = argparse.ArgumentParser(prog='mpex')

    # create sub parsers
    subparsers = parser.add_subparsers()
    init_init(subparsers)
    init_reinit(subparsers)
    init_finalise(subparsers)
    init_group(subparsers)
    init_sync(subparsers)
    init_copy(subparsers)
    init_command(subparsers)
    init_show(subparsers)
    init_edit(subparsers)
    init_set_host(subparsers)
    init_migrate(subparsers)

    # parse arguments and call function
    args = parser.parse_args()

    if hasattr(args, "func"):
        # if everything is OK, call the function
        try:
            args.func(args)
        except (KeyboardInterrupt, application.InterruptedException):
            print()
            print("interrupted")
            sys.exit(2)

    else:
        # print a warning
        parser.print_usage()
        print("Error: too few arguments")
