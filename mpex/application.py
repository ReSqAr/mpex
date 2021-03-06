import io
import os.path
import subprocess
# check python version
import sys

if sys.version_info < (3, 2, 0):
    raise RuntimeError("Python version >= 3.2 is needed.")

from . import local_repository
from . import structure_host
from . import structure_annex
from . import structure_repository
from . import structure_connection
from .lib.terminal import print_red


class InterruptedException(Exception):
    pass


class Application:
    # verbose constants
    VERBOSE_DEBUG = 0
    VERBOSE_NORMAL = 1
    VERBOSE_IMPORTANT = 2

    InterruptedException = InterruptedException

    def __init__(self, path, verbose=True, simulate=False):
        # save option
        self.path = path
        self.verbose = verbose
        self.simulate = simulate

        # initialise hosts
        self.hosts = structure_host.Hosts(self)
        # initialise annexes
        self.annexes = structure_annex.Annexes(self)
        # initialise repositories
        self.repositories = structure_repository.Repositories(self)
        # initialise connections
        self.connections = structure_connection.Connections(self)

        # post load checks
        self.repositories.check()

        # we want to have a new version
        assert self.git_annex_capabilities["date"] >= (2014, 1, 1)

    def save(self):
        """ saves all data """
        self.hosts.save()
        self.annexes.save()
        self.repositories.save()
        self.connections.save()

    def current_host(self):
        """ get the current host """
        # compute path
        path = os.path.join(self.path, "current_hostname")
        # if the path does not exist
        if not os.path.isfile(path):
            raise RuntimeError("Unable to find the current host. (File does not exist)")
        with io.open(path, mode="rt", encoding="UTF8") as fd:
            # read
            hostname = fd.read()
        hostname = hostname.strip()
        # associate host to a Host object
        host = self.hosts.get(hostname)
        # if we failed, raise an error
        if host is None:
            raise RuntimeError("Unable to find the current host. (File: %s)" % hostname)
        # otherwise, return the found host
        return host

    def set_current_host(self, host):
        """ set the current host """
        # compute path
        path = os.path.join(self.path, "current_hostname")
        with io.open(path, mode="wt", encoding="UTF8") as fd:
            # write
            fd.write(host.name)

    @staticmethod
    def assimilate(repo, connection=None):
        """ promotes a Repository to a LocalRepository """
        # promote the object
        return local_repository.LocalRepository(repo, connection)

    def get_hosted_repositories(self):
        """ get all repositories which are hosted on the current machine """
        return {self.assimilate(repo) for repo in self.current_host().repositories()}

    def get_connections(self):
        """ get all connections which originate from the current host """
        return self.current_host().connections()

    def get_connected_repositories(self, conn):
        """ find all repositories which are connected via the given connection """
        return {self.assimilate(repo, conn) for repo in conn.dest.repositories()}

    @property
    def git_annex_capabilities(self):
        """
            checks if the current git annex version supports certain
            operations, e.g. direct mode, certain special remotes, etc.
        """

        # if there is a cache, use it
        if hasattr(self, "_gitAnnexCapabilities_Cache"):
            return self._gitAnnexCapabilities_Cache

        capabilities = {}

        # call git annex
        version_string = subprocess.check_output(["git-annex", "version"])
        version_string = version_string.decode("UTF8").split("ubuntu")[0]

        for line in version_string.splitlines():
            # extract the line 'git-annex version: *'
            s = "git-annex version:"
            if s in line:
                capabilities["version"] = line[len(s):].strip()

        # parse the version string
        date = capabilities["version"].split('.')[1]
        if "-" in date:
            date = date.split("-")[0]
        assert len(date) == 8, "Version string is unexpected format: %s" % capabilities["version"]
        year, month, day = date[:4], date[4:6], date[6:]
        year, month, day = int(year), int(month), int(day)
        capabilities["date"] = year, month, day

        # cache it
        self._gitAnnexCapabilities_Cache = capabilities

        # return
        return capabilities

    def execute_command(self, cmd, ignore_exception=False, print_ignored_exception=True):
        """ print and execute the command """
        if self.verbose <= self.VERBOSE_IMPORTANT:
            print("command:", " ".join(cmd))

        # if we only simulate, return
        if self.simulate:
            print("simulation: command not executed")
            return

        try:
            with open(os.devnull, "w") as devnull:
                subprocess.check_call(cmd, stdout=None if self.verbose <= self.VERBOSE_NORMAL else devnull)
        except (subprocess.CalledProcessError, OSError) as e:
            if ignore_exception:
                if print_ignored_exception:
                    print_red("an ignored error occurred:", str(e))
            else:
                print_red("an error occurred:", str(e))
                raise InterruptedException(e)
