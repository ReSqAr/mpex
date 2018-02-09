import collections
import datetime
import json
import os
import subprocess

from .lib.terminal import print_blue, print_red


class GitRepository:
    @property
    def local_path(self):
        raise NotImplementedError

    #
    # file system interaction
    #
    def execute_command(self, cmd, ignore_exception=False, print_ignored_exception=True):
        """ print and execute the command """

        # use the method given by the application
        self.app.execute_command(cmd, ignore_exception=ignore_exception,
                                 print_ignored_exception=print_ignored_exception)

    def change_path(self, create=False):
        """ change the path to the current repository """

        # get path
        path = os.path.normpath(self.local_path)

        if create:
            # create the path if needed
            if not os.path.isdir(path):
                os.makedirs(path)
        elif not os.path.isdir(os.path.join(path, ".git/annex")):
            # if we are not allowed to create it, it has to be git annex archive
            print_red("%s is not a git annex repository, please run 'mpex init' first." % path, sep='')
            raise self.app.InterruptedException("this is not a git annex repository")

        # change to it
        os.chdir(path)

        # make really sure that we are, where we want to be
        assert os.path.normpath(os.getcwd()) == path, "We are in the wrong directory?!?"

        return path

    def git_config(self, key, default=None):
        """ read a git key """
        # change path
        self.change_path()

        try:
            # get output of 'git config $key' and return it
            output = subprocess.check_output(["git", "config", key]).decode("UTF-8").strip()
            assert output, "Error."
            return output
        except subprocess.CalledProcessError:
            return default

    def git_branch(self):
        """ returns all known branches """
        # change path
        self.change_path()

        # call 'git branch'
        output = subprocess.check_output(["git", "branch"]).decode("UTF8")
        # the first two characters are noise
        return [line[2:].strip() for line in output.splitlines() if line.strip()]

    @staticmethod
    def git_head():
        """ get the git HEAD of the master branch """
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()

    def git_remotes(self):
        """ find all git remotes """

        # change into the right directory
        self.change_path()

        # read all remotes
        cmd = ["git", "remote", "show"]
        output = subprocess.check_output(cmd).decode("UTF-8")
        return {remote.strip() for remote in output.splitlines()}


class GitAnnexRepository(GitRepository):
    def standard_repositories(self):
        raise NotImplementedError

    def git_annex_info(self):
        """ calls 'git-annex info --fast --json' and parses the output """
        # change path
        self.change_path()

        # call the command
        cmd = ["git-annex", "info", "--fast", "--json"]
        with open(os.devnull, "w") as devnull:
            output = subprocess.check_output(cmd, stderr=devnull).decode("UTF-8")

        # parse output
        info = json.loads(output)

        return info

    def get_annex_UUID(self):
        """ get the git annex uuid of the current repository """
        return self.git_config("annex.uuid")

    def git_annex_status(self):
        """ call 'git annex status' """
        # change into the right directory
        self.change_path()

        # get status
        cmd = ["git", "annex", "status", "--json"]

        # call command
        output = subprocess.check_output(cmd).decode("UTF-8")
        data = [json.loads(s) for s in output.split("\n") if s]
        print(data)
        # data looks like: list of {"status":"<status>","file":"<name>"}
        return data

    def has_uncommitted_changes(self):
        """
            has the current repository uncommitted changes?
            warning: has_uncommitted_changes is inaccurate for direct
                     repositories as a type change can mask a content change
        """
        # accept all except type changes
        return any(data["status"] != 'T' for data in self.git_annex_status())

    def on_disk_direct_mode(self):
        """ finds the on disk direct mode """

        # get the config entry for 'annex.direct'
        direct = self.git_config("annex.direct", "false")

        # translate it to 'direct'/'indirect'
        return "direct" if direct == "true" else "indirect"

    def on_disk_trust_level(self):
        """ determines the current trust level """

        # get git annex info and git annex uuid
        uuid = self.get_annex_UUID()
        info = self.git_annex_info()

        for level in self.TRUST_LEVEL:
            # create key
            key = "%sed repositories" % level

            # if there is repository on the current trust level, ignore it
            if key not in info:
                continue

            # read the list of repositories
            # format: dictionary with keys:
            # - description -> git id (desc) or desc
            # - here -> bool
            # - uuid -> uuid
            repos = info[key]

            for repo in repos:
                # find the repository with our current uuid
                if repo["uuid"] == uuid:
                    return level
        else:
            raise ValueError("Unable to determine the trust level.")

    def on_disk_description(self):
        """ find the on disk description of the current repository """
        """ determines the current trust level """

        # get git annex info and git annex uuid
        uuid = self.get_annex_UUID()
        info = self.git_annex_info()

        for level in self.TRUST_LEVEL:
            # create key
            key = "%sed repositories" % level

            # if there is repository on the current trust level, ignore it
            if key not in info:
                continue

            # read the list of repositories
            # format: dictionary with keys:
            # - description -> git id (desc) or desc
            # - here -> bool
            # - uuid -> uuid
            repos = info[key]

            for repo in repos:
                # find the repository with our current uuid
                if repo["uuid"] == uuid:
                    # format as indicated above
                    if '(' in repo["description"]:
                        return repo["description"].split("(", 1)[1][:-1]
                    else:
                        return repo["description"]
        else:
            raise ValueError("Unable to determine the current description.")

    def missing_git_remotes_check(self, repos):
        """ check that all given repositories are indeed registered as a git remote """
        # get registered git remotes
        remotes = self.git_remotes()

        # compute the missing ones
        missing = {r for r in repos if r.gitID() not in remotes}

        # if none are missing, everything is alright
        if not missing:
            return

        # otherwise warn the user
        print_red("the following repositories are not registered, consider running 'mpex reinit'", sep='')
        for r in sorted(missing, key=lambda r: str((r.host, r.annex, r.path))):
            print("Host: %s Annex: %s Path: %s" % (r.host.name, r.annex.name, r.path))
            # there is something additional to be told in the case of special repositories
            if r.is_special():
                print_red("warning: this is a special remote, you have to enable it manually", sep='')
                print("create the special remote with the following command:")
                print("    git annex initremote %s mac=HMACSHA512 encryption=<key> type=<type> ..." % r.gitID())
                print("activate an already existing special remote with the following command:")
                print("    git annex enableremote %s" % r.gitID())
                print("NEVER create a special remote twice.")

        # bail out
        raise self.app.InterruptedException("there are missing git remotes")

    #
    # main methods
    #
    def init(self, ignore_nonempty=False):
        """ inits the repository """

        if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
            print_blue("initialise", self.annex.name, "at", self.local_path)

        # change into the right directory, create it if necessary
        self.change_path(create=True)

        # init git
        if not os.path.isdir(os.path.join(self.local_path, ".git")):
            if os.listdir(self.local_path) and not ignore_nonempty:
                print_red("trying to run 'git init' in a non-empty directory, use --ignorenonempty", sep='')
                raise self.app.InterruptedException("non-empty directory")
            else:
                self.execute_command(["git", "init"])
        else:
            if self.app.verbose <= self.app.VERBOSE_NORMAL:
                print("It is already a git repository.")

        # init git annex
        if not os.path.isdir(os.path.join(self.local_path, ".git/annex")):
            self.execute_command(["git-annex", "init", self.description])
        else:
            if self.app.verbose <= self.app.VERBOSE_NORMAL:
                print("It is already a git annex repository.")

        # set the properties
        self.set_properties()

    def set_properties(self):
        """ sets the properties of the current repository """

        if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
            print_blue("setting properties of", self.annex.name, "at", self.local_path)

        # change into the right directory
        self.change_path()

        # make sure that the master branch exists
        self.repair_master()

        # set the description, if needed
        if self.on_disk_description() != self.description:
            cmd = ["git-annex", "describe", "here", self.description]
            self.execute_command(cmd)

        # set the requested direct mode, change only if needed
        d = "direct" if self.direct else "indirect"
        if self.on_disk_direct_mode() != d:
            self.execute_command(["git-annex", d])

        # set trust level if necessary
        if self.on_disk_trust_level() != self.trust:
            self.execute_command(["git-annex", self.trust, "here"])

        # set git remotes
        # note: it only adds connections to repositories which are currently accesible
        # furthermore, it does not delete connections
        for repo, connections in self.standard_repositories().items():
            # ignore special repositories
            if repo.is_special():
                continue

            # make sure that we have only one connection
            assert connections, "Programming error."
            assert len(connections) == 1, "Git supports only up to one connection."

            # select connection and get details
            connection = connections.pop()
            gitID = repo.gitID()
            # determine the git path
            if connection is None:
                # if it is local, use the path
                git_path = repo.path
            else:
                # otherwise delegate this question to the connection
                git_path = connection.git_path(repo)

            try:
                # determine which url was already set
                url = self.git_config("remote.%s.url" % gitID)
            except subprocess.CalledProcessError:
                # no url was yet set
                url = None

            if not url:
                # if no url was yet set, set it
                self.execute_command(["git", "remote", "add", gitID, git_path])
            elif url != git_path:
                # if the url was incorrect, warn the user and reset it
                print_red("The url set for the connection %s does not match the computed one: %s != %s"
                          % (connection, url, git_path))
                # remove the old url and set it again
                self.execute_command(["git", "remote", "remove", gitID])
                self.execute_command(["git", "remote", "add", gitID, git_path])
            else:
                # if everything is alright
                continue

    def finalise(self):
        """ calls git-annex add and commits all changes """

        if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
            print_blue("commiting changes in", self.annex.name, "at", self.local_path)

        # change into the right directory
        self.change_path()

        # call 'git-annex add'
        self.execute_command(["git-annex", "add"])

        # commit it
        utc = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")
        msg = "Host: %s UTC: %s" % (self.host.name, utc)
        try:
            # there is no good way of checking if the repository needs a commit
            self.execute_command(["git-annex", "sync", "--no-push", "--no-pull", "--message={}".format(msg)])
        except:
            pass

    def sync(self, repositories=None):
        """
            calls finalise and git-annex sync, when repositories is given, sync
            only with those, otherwise with all connected repositories insted
        """
        # finalise repository
        self.finalise()

        # make sure that the master branch exists
        self.repair_master()

        if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
            print_blue("syncing", self.annex.name, "in", self.local_path)

        # change into the right directory
        self.change_path()

        # repositories to sync with (select only non-special repositories)
        sync_repos = set(repo for repo in self.standard_repositories().keys() if not repo.is_special())

        # check that all these repositories are registered
        self.missing_git_remotes_check(sync_repos)

        # only select wanted repositories
        if repositories is not None:
            sync_repos &= set(repositories)

        if sync_repos:
            # call 'git-annex sync $gitIDs'
            gitIDs = [repo.gitID() for repo in sorted(sync_repos, key=str)]
            self.execute_command(["git-annex", "sync"] + gitIDs)
        else:
            # if no other annex is available, still do basic maintanence
            self.execute_command(["git-annex", "merge"])

    def repair_master(self):
        """ creates the master branch if necessary """

        # change into the right directory
        self.change_path()

        branches = self.git_branch()
        # unneeded, if the master branch already exists
        if "master" in branches:
            return

        # we have to use this
        # (http://git-annex.branchable.com/direct_mode/)
        self.execute_command(["git", "-c", "core.bare=false", "commit", "--allow-empty", "-m", "empty commit"])

    def copy(self, copy_all=False, repositories=None, files=None, strict=None):
        """
            copy files, arguments:
            - copy_all: call git annex with the --all flag
            - repositories: target repositories, if the default is given, then all are used
            - files: expression which specifies which files should be transfered,
                     defaults to the local repositories files entry, if nothing is given,
                     all files are transfered
            - strict: drop all files which do not match the local files expression
        """

        # use files expression of the current repository, if none is given
        if files is None:
            local_files_cmd = self.files_as_cmd()
        else:
            local_files_cmd = self._files_as_cmd(files)

        # repositories to copy from and to
        repos = set(self.standard_repositories().keys())

        # check that all these repositories are registered
        self.missing_git_remotes_check(repos)

        # only select wanted repositories
        if repositories is not None:
            repos &= set(repositories)

        # check remote files expression
        for repo in sorted(repos, key=str):
            # if we can convert it to command line arguments, then everything is fine
            _ = repo.files_as_cmd()

        # sync
        self.sync(repos)

        if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
            print_blue("copying files of", self.annex.name, "at", self.local_path)

        # change into the right directory
        self.change_path()

        #
        # pull
        #

        # compute flags which should be used:
        #   --fast and --all (if available and wanted)
        # rationale:
        #   --fast: we are synced
        flags = ["--fast"]
        if copy_all:
            flags.append("--all")

        # call 'git-annex copy --fast [--all] --from=target <files expression as command>'
        for repo in sorted(repos, key=str):
            cmd = ["git-annex", "copy"] + flags + ["--from=%s" % repo.gitID()] + local_files_cmd
            self.execute_command(cmd)

        #
        # push
        #

        for repo in sorted(repos, key=str):
            # parse remote files expression
            files_cmd = repo.files_as_cmd()

            # call 'git-annex copy --fast [--all] --to=target <files expression as command>'
            cmd = ["git-annex", "copy"] + flags + ["--to=%s" % repo.gitID()] + files_cmd
            self.execute_command(cmd)

        #
        # apply strict
        #

        # use strict of the current repository, if none is given
        if strict is None:
            strict = self.strict

        if strict:
            # call 'git-annex drop --not -( <files expression -)
            cmd = ["git-annex", "drop"] + ["--not", "-("] + local_files_cmd + ["-)"]
            self.execute_command(cmd, ignore_exception=True)

        # apply strict for remote repositories
        for repo in sorted(repos, key=str):
            # only apply if wanted
            if not repo.strict:
                continue
            # parse remote files expression
            files_cmd = repo.files_as_cmd()

            # call 'git-annex drop --from=target --not -( <files expression> -)
            cmd = ["git-annex", "drop", "--from=%s" % repo.gitID()] + ["--not", "-("] + files_cmd + ["-)"]
            self.execute_command(cmd, ignore_exception=True)

        # sync again
        self.sync(repos)

    def delete_all_remotes(self):
        """
            deletes all remotes found in .git/config, this implicitly deletes
            also all remote tracking-branches
        """

        if self.app.verbose <= self.app.VERBOSE_IMPORTANT:
            print_blue("delete all remotes of", self.annex.name, "in", self.local_path)

        # change path to current directory
        self.change_path()

        # find all remotes
        remotes = self.git_remotes()
        if self.app.verbose <= self.app.VERBOSE_NORMAL:
            print("remotes found: %s" % ', '.join(remotes))

        # delete all remotes
        for remote in remotes:
            cmd = ["git", "remote", "rm", remote]
            self.execute_command(cmd)


class LocalRepository(GitAnnexRepository):
    """
        LocalRepository represents a realisation of a repository
        which can be accessed from app.currentHost()
        
        main git annex methods:
            init(ignore_nonempty=False)
            set_properties()
            finalise()
            sync(annex descriptions=None)
            repair_master()
            copy(annex descriptions, files expression, strict=true/false)
            delete_all_remotes()

        git methods:
            git_config(key) -> value
            git_branch() -> list of branches
            git_head() -> git head
        
        git annex methods:
            git_annex_info()
            get_annex_UUID()
            git_annex_status()
            on_disk_direct_mode()
            on_disk_trust_level()
            on_disk_description()
            
        other methods:
            change_path()
            standard_repositories()
    """

    def __init__(self, repo, connection=None):
        # call super
        super(LocalRepository, self).__init__()

        # save options
        self.repo = repo
        self.connection = connection

        # check that the gurantees are valid, i.e. it is reachable via
        if self.connection:
            # if it is a remote repository, check the integrity of the arguments
            assert self.app.current_host() == self.connection.source, \
                "the connection does not originate from the current host. (%s != %s)" \
                % (self.app.current_host(), self.connection.source)
            # the connection should end at the host of the current repository
            assert repo.host == connection.dest, \
                "the connection does not end at the host of the current repository. (%s != %s)" \
                % (self.repo.host, self.connection.dest)
            # the connection has to be local
            assert self.connection.is_local(), \
                "the connection has to be to 'local'."
        else:
            # otherwise, the repository is hosted on the current host
            assert self.app.current_host() == self.repo.host, \
                "the repository is not hosted on the current host. (%s != %s)" \
                % (self.app.current_host(), self.repo.host)

    def __getattribute__(self, name):
        """ forward request to self.repo """
        try:
            # try to satisfy the request via self.repo
            return getattr(self.repo, name)
        except:
            # otherwise, satisfy the request locally
            return super(LocalRepository, self).__getattribute__(name)

    def __setattr__(self, name, v):
        """ forward request to self.repo """
        try:
            # if repo has a variable called name, then set it there
            if hasattr(self.repo, name):
                return setattr(self.repo, name, v)
        except AttributeError:
            # no attribute named repo
            pass
        # otherwise, set it here
        return super(LocalRepository, self).__setattr__(name, v)

    @property
    def local_path(self):
        """ returns the path on the local machine """
        assert not self.is_special(), "local path can only be called for non-special remotes"

        if self.connection is None:
            # the repository is on the local machine
            return self.path
        else:
            # we are working remotely: give the path on the local machine
            return self.connection.path_on_source(self.path)

    def standard_repositories(self):
        """ determine repositories which are online (from the point of view of the current host) """
        # convert connections to a dictionary dest -> set of connections to dest
        connections = collections.defaultdict(set)
        for connection in self.app.current_host().connections():
            connections[connection.dest].add(connection)

        # add trivial connection from the current host!
        connections[self.host].add(None)

        # get repositories
        repositories = self.annex.repositories()

        # get the repositories which are online
        active_repos = collections.defaultdict(set)

        for repository in repositories:
            # filter out the current repository
            if repository == self:
                continue

            for connection in connections[repository.host]:
                if connection is None:
                    # we are working locally, add the connection only if
                    # the repository is non-special, i.e. avoid implcit
                    # connections to special local repositories
                    if not repository.is_special():
                        active_repos[repository].add(connection)
                elif connection.is_online():
                    # add the connection if the connection is online
                    active_repos[repository].add(connection)

        return active_repos
