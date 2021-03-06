import itertools
import os.path
import subprocess
import tempfile
import unittest

from mpex import application

# show everything, errors may hide in the output branches
verbose = 0


# noinspection PyUnusedLocal
class TestStructure(unittest.TestCase):
    """
        tests structural properties of the application
    """
    verbose = verbose

    def setUp(self):
        # create temporary directory
        self.path = tempfile.mkdtemp()

    def tearDown(self):
        # erase variable
        self.path = None

    # available methods:
    # - assertFalse, assertTrue
    # - assertEqual
    # - assertRaises
    # - assertIn
    # - assertCountEqual
    # - assertIsNotNone

    def test_app_creation(self):
        app = application.Application(self.path, verbose=self.verbose)
        self.assertIsNotNone(app)

    def test_hosts_creation(self):
        """ test host creation and identity """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections

        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]
        host1p = h.get("Host1")

        self.assertEqual(host1, host1p)
        self.assertEqual(id(host1), id(host1p))

        self.assertEqual(h.get_all(), {host1, host2, host3})

    def test_hosts_creation_error_cases(self):
        """ test common error cases """

        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections

        self.assertRaisesRegex(AssertionError, "empty", h.create, "")
        self.assertRaisesRegex(AssertionError, "invalid character", h.create, "ü")
        self.assertRaisesRegex(AssertionError, "white space", h.create, " ")

    def test_creation_annexes(self):
        """ test annex creation and identity """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections

        # creation
        annex1, annex2, annex3 = [a.create("Annex%d" % i) for i in range(1, 4)]
        annex1p = a.get("Annex1")

        # identity
        self.assertEqual(annex1, annex1p)
        self.assertEqual(id(annex1), id(annex1p))

        self.assertEqual(a.get_all(), {annex1, annex2, annex3})

        # test repr and str
        repr(annex1)
        str(annex1)

    def test_creation_annexes_error_cases(self):
        """ test common error cases """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections

        self.assertRaisesRegex(AssertionError, "empty", a.create, "")
        self.assertRaisesRegex(AssertionError, "invalid character", a.create, "ü")
        self.assertRaisesRegex(AssertionError, "white space", a.create, " ")

    def test_creation_repositories(self):
        """ test creation of repositories """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]
        annex1, annex2, annex3 = [a.create("Annex%d" % i) for i in range(1, 4)]

        # creation
        repo11 = r.create(host1, annex1, os.path.join(self.path, "repo11"))
        repo12 = r.create(host1, annex2, os.path.join(self.path, "repo12"))
        repo13 = r.create(host1, annex3, os.path.join(self.path, "repo13"))
        repo21 = r.create(host2, annex1, os.path.join(self.path, "repo11"))
        repo22 = r.create(host2, annex2, os.path.join(self.path, "repo22"))
        repo23 = r.create(host2, annex3, os.path.join(self.path, "repo23"))
        repo33 = r.create(host3, annex3, os.path.join(self.path, "repo33"))
        repo11p = r.get(host1, annex1, os.path.join(self.path, "repo11"))

        # identity (equal if host and path are equal)
        self.assertEqual(repo11, repo11p)
        self.assertEqual(id(repo11), id(repo11p))

        self.assertEqual(r.get_all(), {repo11, repo12, repo13, repo22, repo33, repo23, repo21})

        # test repr and str
        repr(repo11)
        str(repo11)

    def test_creation_repositories_error_cases(self):
        """ """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host1up = h.create("Host1"), h.create("HOST1")
        annex1 = a.create("Annex1")
        # test error conditions
        # use repoxx, some paths are already taken, hence the identity map applies
        rxx = os.path.join(self.path, "repoxx")
        self.assertRaisesRegex(AssertionError, "Host", r.create,
                               "", annex1, rxx)
        self.assertRaisesRegex(AssertionError, "Annex", r.create,
                               host1, "", rxx)
        self.assertRaisesRegex(AssertionError, "absolute", r.create,
                               host1, annex1, "tmp")
        self.assertRaisesRegex(AssertionError, "non-empty", r.create,
                               host1, annex1, rxx, description="")
        self.assertRaisesRegex(AssertionError, "invalid", r.create,
                               host1, annex1, rxx, description="ü")
        self.assertRaisesRegex(AssertionError, "trust has to be valid", r.create,
                               host1, annex1, rxx, trust="unknown")

        # get should raise an error
        self.assertRaises(KeyError, r.get,
                          host1, annex1, os.path.join(self.path, "repo11"))

        # indeed create repositories
        repo11 = r.create(host1, annex1, os.path.join(self.path, "repo11"))
        repo11up = r.create(host1up, annex1, os.path.join(self.path, "repo11"))

        # recreate should give an error
        self.assertRaisesRegex(AssertionError, "already exists", r.create,
                               host1, annex1, os.path.join(self.path, "repo11"))
        self.assertRaisesRegex(AssertionError, "already exists", r.create,
                               host1up, annex1, os.path.join(self.path, "repo11"), description=host1.name)

        # get should give the same element
        repo11p = r.get(host1, annex1, os.path.join(self.path, "repo11"))
        self.assertEqual(repo11, repo11p)

        # files cannot be checked on initialisation, so check only <repo>.files = <expr>
        self.assertRaisesRegex(ValueError, "non-closed", setattr,
                               repo11, "files", "'")
        self.assertRaisesRegex(ValueError, "no candidates", setattr,
                               repo11, "files", "Host5")
        self.assertRaisesRegex(ValueError, "too many candidates", setattr,
                               repo11, "files", "host1")
        self.assertRaisesRegex(ValueError, "too many '[)]'", setattr,
                               repo11, "files", "(())())")
        self.assertRaisesRegex(ValueError, "too many '[(]'", setattr,
                               repo11, "files", "(())(")

    def test_creation_repositories_metadata_default(self):
        """ check default values """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, annex1 = h.create("Host1"), a.create("Annex1")

        # default value
        repo = r.create(host1, annex1, os.path.join(self.path, "repo"))
        self.assertFalse(repo.direct)
        self.assertFalse(repo.strict)
        self.assertEqual(repo.trust, "semitrust")
        self.assertIsNone(repo.files)
        self.assertFalse(repo.is_special())
        self.assertFalse(repo.has_non_trivial_description())

    def test_creation_repositories_metadata_direct(self):
        """ check metadata direct member """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, annex1 = h.create("Host1"), h.create("Host2"), a.create("Annex1")

        # direct
        repo = r.create(host1, annex1, os.path.join(self.path, "repo"), direct="false")
        self.assertFalse(repo.direct)
        repo.direct = True
        self.assertTrue(repo.direct)

        repo = r.create(host2, annex1, os.path.join(self.path, "repo"), direct="true")
        self.assertTrue(repo.direct)
        repo.direct = False
        self.assertFalse(repo.direct)

    def test_creation_repositories_metadata_strict(self):
        """ check metadata strict member """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, annex1 = h.create("Host1"), h.create("Host2"), a.create("Annex1")

        # strict
        repo = r.create(host1, annex1, os.path.join(self.path, "repo"), strict="false")
        self.assertFalse(repo.strict)
        repo.strict = True
        self.assertTrue(repo.strict)

        repo = r.create(host2, annex1, os.path.join(self.path, "repo"), strict="true")
        self.assertTrue(repo.strict)
        repo.strict = False
        self.assertFalse(repo.strict)

    def test_creation_repositories_metadata_trust(self):
        """ check metadata trust member """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, annex1 = h.create("Host1"), h.create("Host2"), a.create("Annex1")

        # trust
        repo = r.create(host2, annex1, os.path.join(self.path, "repo"), trust="untrust")
        self.assertEqual(repo.trust, "untrust")
        repo.trust = "semitrust"
        self.assertEqual(repo.trust, "semitrust")

        repo = r.create(host1, annex1, os.path.join(self.path, "repo"), trust="trust")
        self.assertEqual(repo.trust, "trust")

    def test_creation_repositories_metadata_files(self):
        """ check metadata files member """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, annex1 = h.create("Host1"), h.create("Host 2"), a.create("Annex1")

        # files
        repo = r.create(host2, annex1, os.path.join(self.path, "repo"))
        repo = r.create(host1, annex1, os.path.join(self.path, "repo"), files="  +Host1 ")
        self.assertEqual(repo.files, "+ Host1")
        repo.files = " (  'host2' + ) -'host1'"
        self.assertEqual(repo.files, "('Host 2' +) - Host1")
        repo.files = None
        self.assertIsNone(repo.files)
        self.assertNotIn("files", repo._data)
        repo.files = None
        self.assertIsNone(repo.files)

    def test_creation_repositories_metadata_files_to_cmd(self):
        """ check metadata files member """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host, annex1 = h.create("Host"), a.create("Annex1")

        # files
        repo = r.create(host, annex1, os.path.join(self.path, "repo"))
        repo.files = "()+-&host"
        self.assertEqual(repo.files_as_cmd(), ["-(", "-)", "--or", "--not", "--and", "--in=Host"])

    def test_creation_repositories_metadata_description(self):
        """ check metadata description member """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host, annex = h.create("Host"), a.create("Annex")

        # description
        repo = r.create(host, annex, os.path.join(self.path, "repo"), description="XXX")
        self.assertEqual(repo.description, "XXX")
        self.assertTrue(repo.has_non_trivial_description())

    def test_repositories_special(self):
        """ check the isSpecial method """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host, annex = h.create("Host"), a.create("Annex")

        # check special
        repo = r.create(host, annex, "special", description="XXX")
        self.assertTrue(repo.is_special())

    def test_connection_creation(self):
        """ test the creation of connections """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # creation
        conn12 = c.create(host1, host2, "/abc/")
        conn13 = c.create(host1, host3, "/")
        conn23 = c.create(host2, host3, "/")
        conn21 = c.create(host2, host1, "/")
        conn32 = c.create(host3, host2, "ssh://server")
        conn12p = c.get(host1, host2, "/abc/")

        # identity
        self.assertEqual(conn12, conn12p)
        self.assertEqual(id(conn12), id(conn12p))

        self.assertEqual(c.get_all(), {conn12, conn13, conn23, conn21, conn32})

        # test repr and str
        repr(conn12)
        str(conn12)

    def test_connection_creation_error_cases(self):
        """ test common error cases """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        self.assertRaisesRegex(AssertionError, "source", c.create, "", host2, "/")
        self.assertRaisesRegex(AssertionError, "dest", c.create, host1, "", "/")
        self.assertRaisesRegex(ValueError, "protocol", c.create, host1, host2, "xxx")

    def test_connection_metadata_gitPath(self):
        """ test gitPath """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]
        annex1 = a.create("Annex1")
        repo11 = r.create(host1, annex1, os.path.join(self.path, "repo"))
        repo21 = r.create(host2, annex1, os.path.join(self.path, "repo"))

        # create the connections
        conn12 = c.create(host1, host2, "/abc/")
        conn32 = c.create(host3, host2, "ssh://server")

        # test
        self.assertEqual(conn12.git_path(repo21), "/abc" + self.path + "/repo")
        self.assertEqual(conn32.git_path(repo21), "ssh://server" + os.path.join(self.path, "repo"))
        self.assertRaisesRegex(AssertionError, "Programming error", conn32.git_path, repo11)

    def test_connection_metadata_alwayson(self):
        """ test alwaysOn """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # alwayson
        conn12 = c.create(host1, host2, "/", alwayson="false")
        self.assertFalse(conn12.always_on)
        conn12.always_on = True
        self.assertTrue(conn12.always_on)

        conn13 = c.create(host1, host3, "/", alwayson="true")
        self.assertTrue(conn13.always_on)
        conn13.always_on = False
        self.assertFalse(conn13.always_on)

    def test_connection_metadata_protocol(self):
        """ test protocol and pathData """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # protocol 'mount'
        conn1local = c.create(host1, host2, "/")
        self.assertEqual(conn1local.protocol(), "mount")

        # protocol 'ssh' and pathData
        conn1server = c.create(host1, host3, "ssh://myserver")
        self.assertEqual(conn1server.protocol(), "ssh")
        self.assertEqual(conn1server.path_data()["server"], "myserver")

    def test_connection_isonline_mount_nodir(self):
        """ test the isOnline method for connections with protocol 'mount' """
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # connection with a path which does not exists
        conn = c.create(host1, host2, os.path.join(self.path, "repo"))
        self.assertFalse(conn.is_online())

    def test_connection_isonline_mount_emptydir(self):
        """ test the isOnline method for connections with protocol 'mount' """
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # create the connection connection
        conn = c.create(host1, host2, os.path.join(self.path, "repo"))

        # create the path, empty paths should also be not mounted
        os.makedirs(conn.path)
        self.assertFalse(conn.is_online())

    def test_connection_isonline_mount_dir(self):
        """ test the isOnline method for connections with protocol 'mount' """
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # create the connection connection
        conn = c.create(host1, host2, os.path.join(self.path, "repo"))

        # create the path
        os.makedirs(conn.path)

        # create a file, then the directory is mounted
        with open(os.path.join(conn.path, "test"), "wt") as fd:
            fd.write("test")

        # should return True
        self.assertTrue(conn.is_online())

    def test_connection_isonline_ssh(self):
        """ test the isOnline method for connections with protocol 'ssh' """
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # connection with a server which does not exist
        conn = c.create(host1, host2, "ssh://127.0.0.1:53122")
        self.assertFalse(conn.is_online())
        # second time comes from cache
        self.assertFalse(conn.is_online())

    def test_connection_pathOnSource(self):
        """ test the pathOnSource method for connections with protocol 'ssh' """
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # create connection
        conn12 = c.create(host1, host2, "/test/")
        self.assertEqual(conn12.path_on_source("/abc/"), "/test/abc/")

        # create connection
        conn23 = c.create(host2, host3, "/test")
        self.assertEqual(conn12.path_on_source("/abc/"), "/test/abc/")

    def test_connection_remote_execution(self):
        """ test the and supportsRemoteExecution and executeRemotely methods """
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]

        # create connection
        conn12 = c.create(host1, host2, "/test/")
        self.assertFalse(conn12.supports_remote_execution())
        self.assertRaisesRegex(AssertionError, "does not support remote execution",
                               conn12.execute_remotely, ["ls"])

        # create connection
        conn23 = c.create(host2, host3, "ssh://myserver")
        self.assertTrue(conn23.supports_remote_execution())
        self.assertRaisesRegex(AssertionError, "expected a list", conn23.execute_remotely, "ls")

        # we can only check the resulting command, so overwrite app.executeCommand
        subroutine_called = []

        def check_execute_command(cmd):
            subroutine_called.append(True)
            self.assertEqual(cmd, ["ssh", "myserver", "ls"])

        app.execute_command = check_execute_command
        conn23.execute_remotely(["ls"])
        self.assertEqual(subroutine_called, [True])

    def test_relations(self):
        """
            test Host's repositories and connections methods as well as
            Annex's repositories and Repository's connectedRepositories
            methods
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        n = 3
        hosts = [h.create("Host%d" % i) for i in range(1, n + 1)]
        annexes = [a.create("Annex%d" % i) for i in range(1, n + 1)]

        # no connections nor repositories for any host
        for i in range(n):
            self.assertEqual(hosts[i].repositories(), set())
            self.assertEqual(hosts[i].connections(), set())
        # no repositories for any annex
        for i in range(n):
            self.assertEqual(annexes[i].repositories(), set())

        # create every possible host, annex combination
        # first index hosts, second index annexes
        repos = [
            [
                r.create(host,
                         annex,
                         os.path.join(self.path, "repo-%s-%s" % (host.name, annex.name)))
                for annex in annexes
            ]
            for host in hosts
        ]
        # create every possible connection
        # first indexs source, second index destination
        conns = [
            [
                c.create(source, dest, "/")
                for dest in hosts
                if source != dest
            ]
            for source in hosts
        ]

        # test relational methods
        for i in range(n):
            # hosts[i].repositories() should be all repositories hosted
            # by hosts[i], hence {repos[i][j] for all j}
            self.assertEqual(hosts[i].repositories(), set(repos[i]))
            # hosts[i].connections() should be all connections which
            # originate from hosts[i], hence {conns[i][j] for all j}
            self.assertEqual(hosts[i].connections(), set(conns[i]))

        for i in range(n):
            # annexes[i].repositories() should be all repositories which
            # belong to this annex, hence {repos[j][i] for all j}
            self.assertEqual(annexes[i].repositories(), {r_on_h[i] for r_on_h in repos})

        for i in range(n):
            for j in range(n):
                # current host: hosts[i]
                # current annex: annexes[j]

                # create a dictionary of the following form:
                # repository (belonging annexes[j]), hence repos[k][j] for all k
                # -> connection from repos[k][j].host = host[k] to host[i], i.e.
                # conns[i][k] for k < i or conns[i][k-1] for k > i (and ignore i = k)
                d = {
                    repos[k][j]:
                        {conns[i][k if k < i else k - 1]}
                    for k in range(n) if k != i
                }

                # they should be equal
                self.assertEqual(repos[i][j].connected_repositories(), d)

    def test_save(self):
        """
            test save and load procedures and that they are an identity operation
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections

        # create objects
        host1 = h.create("Host1")
        host2 = h.create("Host2")
        host3 = h.create("Host3")

        annex1 = a.create("Annex1")
        annex2 = a.create("Annex2")
        annex3 = a.create("Annex3")

        repo11 = r.create(host1, annex1, os.path.join(self.path, "repo11"), direct="true", strict="true")
        repo12 = r.create(host1, annex2, os.path.join(self.path, "repo12"), files="+host1", trust="untrust")
        repo13 = r.create(host1, annex3, os.path.join(self.path, "repo13"), trust="trust")

        conn12 = c.create(host1, host2, "/", alwayson="true")
        conn13 = c.create(host1, host3, "/")
        conn23 = c.create(host2, host3, "/")

        # save
        app.save()

        # restart
        app = application.Application(self.path, verbose=self.verbose)

        # short cuts
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections

        self.assertEqual(h.get_all(), {host1, host2, host3})
        self.assertEqual(a.get_all(), {annex1, annex2, annex3})
        self.assertEqual(r.get_all(), {repo11, repo12, repo13})
        self.assertEqual(c.get_all(), {conn12, conn13, conn23})

        repo11 = r.get(host1, annex1, os.path.join(self.path, "repo11"))
        repo12 = r.get(host1, annex2, os.path.join(self.path, "repo12"))
        repo13 = r.get(host1, annex3, os.path.join(self.path, "repo13"))
        self.assertTrue(repo11.direct)
        self.assertTrue(repo11.strict)
        self.assertEqual(repo12.files, "+ Host1")
        self.assertEqual(repo12.trust, "untrust")
        self.assertEqual(repo13.trust, "trust")

        conn12 = c.get(host1, host2, "/")
        self.assertTrue(conn12.always_on)

    def test_app_gitAnnexCapabilities(self):
        """ test app.gitAnnexCapabilities """
        app = application.Application(self.path, verbose=self.verbose)

        capabilities = app.git_annex_capabilities
        self.assertIn("date", capabilities)

        # the second call is from a cache
        capabilities2 = app.git_annex_capabilities
        self.assertEqual(id(capabilities), id(capabilities2))


# noinspection PyUnusedLocal
class TestCommands(unittest.TestCase):
    verbose = verbose
    """
        test command aspects of the application
    """

    def __init__(self, *args, **kwargs):
        # call super
        super(TestCommands, self).__init__(*args, **kwargs)
        # does the current git annex version support direct mode?
        app = application.Application("/tmp/", verbose=self.verbose)
        self._gitAnnexCapabilities = app.git_annex_capabilities

    def setUp(self):
        # create temporary directory
        self.path = tempfile.mkdtemp()

    def tearDown(self):
        # erease variable
        self.path = None

    #
    # repo based helper
    #
    @staticmethod
    def apply_to_repos(repos, f):
        """ applys f to every repository on its host """
        ret = []
        for repo in repos:
            repo.app.set_current_host(repo.host)
            ret.append(f(repo))
        return ret

    def assimilate_repos(self, repos):
        """ assimilate the given repos """
        return self.apply_to_repos(repos, lambda r: r.app.assimilate(r))

    def init_repos(self, repos):
        """ init the given repos """
        self.apply_to_repos(repos, lambda r: r.init())

    def reinit_repos(self, repos):
        """ init the given repos """
        self.apply_to_repos(repos, lambda r: r.set_properties())

    def finalise_repos(self, repos):
        """ finalise the given repos """
        self.apply_to_repos(repos, lambda r: r.finalise())

    def sync(self, repos):
        """ syncs the repos """
        self.apply_to_repos(repos, lambda r: r.sync())

    def copy(self, repos):
        """ copies the repos """
        self.apply_to_repos(repos, lambda r: r.copy())

    def sync_and_copy(self, sync_repos, copy_repos):
        """ sync sync_repos, copy copy_repos and sync sync_repos """
        self.sync(sync_repos)
        self.copy(copy_repos)
        self.sync(sync_repos)

    #
    # file system interaction
    #

    # create
    @staticmethod
    def _create_file(path, filename, content):
        """ create file in the given path """
        f_path = os.path.join(path, filename)
        with open(f_path, "wt") as fd:
            fd.write(filename if content is None else content)

    def create_file(self, repo, filename, content=None):
        """ create file in the given repository """
        self._create_file(repo.path, filename, content)

    def create_file_local(self, repo, filename, content=None):
        """ create file in the given repository """
        self._create_file(repo.local_path, filename, content)

    # remove
    @staticmethod
    def _remove_file(path, filename):
        """ removes the given file """
        f_path = os.path.join(path, filename)
        os.remove(f_path)

    def remove_file(self, repo, filename):
        """ removes the given file """
        return self._remove_file(repo.path, filename)

    def remove_file_local(self, repo, filename):
        """ removes the given file """
        return self._remove_file(repo.local_path, filename)

    # has file
    def _has_file(self, path, filename, content):
        """ checks if the path has the given file (with content) """
        f_path = os.path.join(path, filename)
        with open(f_path, "rt") as fd:
            self.assertEqual(fd.read(), filename if content is None else content)

    def has_file(self, repo, filename, content=None):
        """ checks if the repository has the given file (with content) """
        return self._has_file(repo.path, filename, content)

    def has_file_local(self, repo, filename, content=None):
        """ checks if the repository has the given file (with content) """
        return self._has_file(repo.local_path, filename, content)

    # has link
    def _has_link(self, path, filename):
        """ checks if the path has the given file as a link """
        f_path = os.path.join(path, filename)
        self.assertFalse(os.path.isfile(f_path))
        self.assertTrue(os.path.islink(f_path))

    def has_link(self, repo, filename):
        """ checks if the repository has the given file as a link """
        return self._has_link(repo.path, filename)

    def has_link_local(self, repo, filename):
        """ checks if the repository has the given file as a link """
        return self._has_link(repo.local_path, filename)

    #
    # actual tests
    #
    def test_app_getHostedRepositories(self):
        """ test application's getHostedRepositories method """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2 = h.create("Host1"), h.create("Host2")
        annex1, annex2 = a.create("Annex1"), a.create("Annex2")

        repo11 = r.create(host1, annex1, os.path.join(self.path, "repo11"))
        repo21 = r.create(host2, annex1, os.path.join(self.path, "repo21"))
        repo12 = r.create(host1, annex2, os.path.join(self.path, "repo12"))
        repo22 = r.create(host2, annex2, os.path.join(self.path, "repo22"))

        # test app.CurrentHost
        self.assertRaisesRegex(RuntimeError, "Unable to find", app.current_host)

        app.set_current_host(host1)

        # test app.CurrentHost
        self.assertEqual(app.current_host(), host1)

        # save all
        app.save()

        # restart
        app = application.Application(self.path, verbose=self.verbose)

        # test getHostedRepositories (which returns the assimilated version repo1i)
        self.assertEqual({a.repo for a in app.get_hosted_repositories()}, {repo11, repo12})

    def test_init(self):
        """ test repository init and conduct some basic checks """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, annex1 = h.create("Host1"), a.create("Annex1")

        # set host
        app.set_current_host(host1)

        # create & init
        repo = r.create(host1, annex1, os.path.join(self.path, "repo"))
        repo = app.assimilate(repo)
        repo.init()

        # check properties
        self.assertTrue(bool(repo.get_annex_UUID()))
        self.assertEqual(repo.on_disk_direct_mode(), "indirect")
        self.assertEqual(repo.on_disk_trust_level(), "semitrust")

        # check disk format
        self.assertTrue(os.path.isdir(os.path.join(repo.path, ".git")))
        self.assertTrue(os.path.isdir(os.path.join(repo.path, ".git/annex")))

        # init again
        repo.init()

        # check properties again
        self.assertTrue(bool(repo.get_annex_UUID()))
        self.assertEqual(repo.on_disk_direct_mode(), "indirect")
        self.assertEqual(repo.on_disk_trust_level(), "semitrust")

    def test_set_properties_direct(self):
        """ test repository setProperties with direct mode"""
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, annex1 = h.create("Host1"), a.create("Annex1")

        # set host
        app.set_current_host(host1)

        # create
        repo = r.create(host1, annex1, os.path.join(self.path, "repo"), direct="true", trust="trust")
        repo = app.assimilate(repo)

        # check
        self.assertRaisesRegex(application.InterruptedException, "is not a git annex", repo.set_properties)

        # init
        repo.init()

        # check
        self.assertEqual(repo.on_disk_direct_mode(), "direct")
        self.assertEqual(repo.on_disk_trust_level(), "trust")

        # change
        repo.direct = False
        repo.trust = "untrust"
        repo._data["description"] = "DESC"

        # apply changes
        repo.set_properties()

        # check
        self.assertEqual(repo.on_disk_direct_mode(), "indirect")
        self.assertEqual(repo.on_disk_trust_level(), "untrust")
        self.assertEqual(repo.on_disk_description(), "DESC")

    def test_set_properties_notdirect(self):
        """ test repository setProperties without direct mode """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, annex1 = h.create("Host1"), a.create("Annex1")

        # set host
        app.set_current_host(host1)

        # create
        repo = r.create(host1, annex1, os.path.join(self.path, "repo"), trust="trust")
        repo = app.assimilate(repo)

        # check
        self.assertRaisesRegex(application.InterruptedException, "is not a git annex", repo.set_properties)

        # init
        repo.init()

        # check
        self.assertEqual(repo.on_disk_trust_level(), "trust")

        # change
        repo.trust = "untrust"
        repo._data["description"] = "DESC"

        # apply changes
        repo.set_properties()

        # check
        self.assertEqual(repo.on_disk_direct_mode(), "indirect")
        self.assertEqual(repo.on_disk_trust_level(), "untrust")
        self.assertEqual(repo.on_disk_description(), "DESC")

    def test_init_remotes(self):
        """ test repository init and remotes"""
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3, host4 = [h.create("Host%d" % i) for i in range(1, 4 + 1)]
        annex1 = a.create("Annex1")
        conn12 = c.create(host1, host2, "/abc/", alwayson="true")
        conn13 = c.create(host1, host3, "ssh://yeah/", alwayson="true")
        conn14 = c.create(host1, host4, "/xyz", alwayson="true")

        # set host
        app.set_current_host(host1)

        # create & init
        repo1 = r.create(host1, annex1, os.path.join(self.path, "repo1"))
        repo2 = r.create(host2, annex1, os.path.join(self.path, "repo2"))
        repo3 = r.create(host3, annex1, os.path.join(self.path, "repo3"))
        repo4 = r.create(host4, annex1, "special")
        repo1 = app.assimilate(repo1)
        repo1.init()
        repo1.set_properties()

        # check remotes
        self.assertIn("Host2", subprocess.check_output(["git", "remote", "show"]).decode("UTF8"))
        self.assertIn("Host3", subprocess.check_output(["git", "remote", "show"]).decode("UTF8"))
        self.assertNotIn("Host4", subprocess.check_output(["git", "remote", "show"]).decode("UTF8"))
        with open(os.path.join(repo1.path, ".git/config")) as fd:
            x = fd.read()
            self.assertIn("/abc" + repo2.path, x)
            self.assertIn("ssh://yeah" + repo3.path, x)
            self.assertNotIn("/xyz", x)

    def test_init_non_empty(self):
        """ test repository init in non-empty directory """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, annex1 = h.create("Host1"), a.create("Annex1")

        # set host
        app.set_current_host(host1)

        # init non-empty directory
        path = os.path.join(self.path, "repo-nonempty")
        os.makedirs(path)
        with open(os.path.join(path, "test"), "wt") as fd:
            fd.write("test")

        # create
        repo = r.create(host1, annex1, path)
        repo = app.assimilate(repo)

        # try init
        self.assertRaisesRegex(application.InterruptedException, "non-empty directory", repo.init)
        # force creation and check disk format
        repo.init(ignore_nonempty=True)
        self.assertTrue(os.path.isdir(os.path.join(repo.path, ".git/annex")))

    def test_init_remotes_change_location(self):
        """ test repository set properties and changing of the remotes location """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]
        annex1 = a.create("Annex1")
        conn12 = c.create(host1, host2, "/abc/", alwayson="true")

        # set host
        app.set_current_host(host1)

        repo = r.create(host2, annex1, os.path.join(self.path, "repo"))
        repo = r.create(host1, annex1, os.path.join(self.path, "repo"))
        repo = app.assimilate(repo)
        repo.init()

        # set properties
        repo.set_properties()

        # doing bad stuff, still, repo should adapt
        conn12._path = "/abcd/"
        repo.set_properties()

    def finalise_tester(self, direct):
        """
            test finalise in given mode
            procedure:
            1. setup repository
            2. create files
            3. call finalise
            4. afterwards, the file should still be where
            5. everything should committed
            6. delete certain files, move certain other files
            7. there should be uncommitted changes
            8. call finalise
            9. there shouldn't be any uncommitted changes anymore
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host, annex = h.create("Host1"), a.create("Annex1")

        app.set_current_host(host)

        # create, set direct mode & init
        path = os.path.join(self.path, "repo")
        repo = r.create(host, annex, path)
        repo.direct = direct
        repo = app.assimilate(repo)
        repo.init()

        # check direct mode
        self.assertEqual(repo.on_disk_direct_mode(), "direct" if direct else "indirect")

        # create files
        n = 5
        deleted, non_deleted = "going_to_be_deleted_%d", "not_going_to_be_deleted_%d"
        move_before, move_after = "move_before_%d", "move_after_%d"
        for i in range(n):
            self.create_file(repo, non_deleted % i)
            self.create_file(repo, deleted % i)
            self.create_file(repo, move_before % i)

        # test not commited?
        self.assertTrue(repo.has_uncommitted_changes())

        # finalise
        repo.finalise()

        # still there?
        for i in range(n):
            self.has_file(repo, non_deleted % i)
            self.has_file(repo, deleted % i)
            self.has_file(repo, move_before % i)

        # everything commited?
        self.assertFalse(repo.has_uncommitted_changes())

        # remove and move files
        for i in range(n):
            self.remove_file(repo, deleted % i)
            self.remove_file(repo, move_before % i)
            self.create_file(repo, move_after % i, move_before % i)

        # test not commited?
        self.assertTrue(repo.has_uncommitted_changes())

        # finalise
        repo.finalise()

        # everything commited?
        self.assertFalse(repo.has_uncommitted_changes())

    def test_finalise_indirect(self):
        self.finalise_tester(direct=False)

    def test_finalise_direct(self):
        self.finalise_tester(direct=True)

    def test_finalise_and_change(self):
        """ test the detection of changed files """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host, annex = h.create("Host1"), a.create("Annex1")
        app.set_current_host(host)

        # create, set direct mode & init
        path = os.path.join(self.path, "repo")
        repo = r.create(host, annex, path, direct="true")
        repo = app.assimilate(repo)
        repo.init()

        # create file
        self.create_file(repo, "test")

        # finalise
        repo.finalise()

        # get head
        head = repo.git_head()

        # change file
        self.create_file(repo, "test", "changed")

        # finalise
        repo.finalise()

        # something was commited?
        self.assertNotEqual(head, repo.git_head())

    def test_repairMaster_in_empty(self):
        """ call repair master in empty repository """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, annex = h.create("Host1"), h.create("Host2"), a.create("Annex")
        # set host
        app.set_current_host(host1)

        # create & init
        path = os.path.join(self.path, "repo_host1")
        repo = r.create(host1, annex, path, description="test_repo")
        repo = app.assimilate(repo)
        repo.init()

        # should not raise an exception
        repo.repair_master()

    def sync_tester(self, direct):
        """
            test sync with the given direct mode
            procedure:
            1. create two repositories
            2. create file in the first repository
            3. call sync
            4. then a link to the file should exist in the other directory
            5. call sync again
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, annex = h.create("Host1"), h.create("Host2"), a.create("Annex")
        conn12 = c.create(host1, host2, "/", alwayson="true")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="test_repo_1")
        repo1.direct = direct
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2, description="test_repo_2")
        repo2.direct = direct
        repos = [repo1, repo2]

        # assimilate
        repo1, repo2 = repos = self.assimilate_repos(repos)

        # init
        self.init_repos(repos)

        # create file on host1
        self.create_file(repo1, "test")

        # sync changes on host1
        self.sync([repo1])

        # sync changes on host2
        self.sync([repo2])

        # exists?
        self.has_link(repo2, "test")

        # sync changes on host1
        self.sync([repo1])

    def test_sync_direct(self):
        self.sync_tester(direct=True)

    def test_sync_indirect(self):
        self.sync_tester(direct=False)

    def sync_from_remote_tester(self, direct):
        """
            test sync from with the given direct mode
            procedure:
            1. create two repositories
            2. create file in the second first repository
            3. call sync
            4. then a link to the file should exist in the other directory
            5. call sync again
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, annex = h.create("Host1"), h.create("Host2"), a.create("Annex")
        conn12 = c.create(host1, host2, "/", alwayson="true")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="test_repo_1")
        repo1.direct = direct
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2, description="test_repo_2")
        repo2.direct = direct
        repos = [repo1, repo2]

        # assimilate
        repo1, repo2 = repos = self.assimilate_repos(repos)

        # init
        self.init_repos(repos)

        # create file on host2
        self.create_file(repo2, "test")

        # sync changes (reverse repo order such that repo2 gets synced first,
        # otherwise the file is not yet commited and does not get transfered)
        self.sync(reversed(repos))

        # there?
        self.has_link(repo1, "test")

        # sync changes again
        self.sync(repos)

    def test_sync_from_remote_direct(self):
        self.sync_from_remote_tester(direct=True)

    def test_sync_from_remote_indirect(self):
        self.sync_from_remote_tester(direct=False)

    def create_powerset_files(self, paths):
        """ create all possible combinations of files """
        n = len(paths)
        for i in range(1, n + 1):
            # t is an element of the powerset of {1,...,n} with cardinality i
            for t in itertools.combinations(range(n), i):
                # compute file name
                name = "file_%s" % "".join(str(x + 1) for x in t)
                # create files in the individual paths
                for j in t:
                    path = paths[j]
                    f_path = os.path.join(path, name)
                    if self.verbose:
                        print(f_path)
                    with open(f_path, "wt") as fd:
                        fd.write(name)

        # consistency check
        self.check_powerset_files(paths, lambda t_, f_: self.assertEqual(f_, t_))

    def check_powerset_files(self, paths, checker):
        """
            checks in which directories the files are available,
            checker is a callback function with signature:
            checker(<element of powerset>, <number of the directories where
                                            the file is available>)
        """
        n = len(paths)
        for i in range(1, n + 1):
            # t is an element of the powerset of {1,...,n} with cardinality i
            for t in itertools.combinations(range(n), i):
                # compute file name
                name = "file_%s" % "".join(str(x + 1) for x in t)
                found = set()
                for j, path in enumerate(paths):
                    # check where the files exists
                    f_path = os.path.join(path, name)
                    if os.path.isfile(f_path):
                        # if it exists checks that it has the correct content
                        with open(f_path, "rt") as fd:
                            self.assertEqual(fd.read(), name)
                        found.add(j)

                print("%s found in: %s" % (name, ", ".join(str(x + 1) for x in found)))

                # callback
                checker(set(t), found)

    def test_copy(self):
        """
            test copy
            procedure:
            1. create three repositories with this connections:
               alice (repo2) -> share (repo1) <- bob (repo3)
               share has set as files expression: '(alice - bob) + (bob - alice)'
               and strict flag set
            2. create files in all possible repository combinations
            3. sync all
            4. call copy in repository repo2 and repo3 (in this order)
            5. sync again
            6. now the distribution of the files looks like that:
               share: the file which was only in bob's repository (file_3)
               alice: all except the file which was only in bob's repository (file_3)
               bob:   all files
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]
        annex = a.create("Annex")
        conn12 = c.create(host2, host1, "/", alwayson="true")
        conn13 = c.create(host3, host1, "/", alwayson="true")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="repo: share",
                         files="(repo:alice - repo:bob) + (repo:bob - repo:alice)", strict="true")
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2, description="repo: alice")
        path3 = os.path.join(self.path, "repo_host3")
        repo3 = r.create(host3, annex, path3, description="repo: bob")

        paths = [path1, path2, path3]
        repos = [repo1, repo2, repo3]

        # assimilate
        repo1, repo2, repo3 = repos = self.assimilate_repos(repos)

        # init repos
        self.init_repos(repos)

        # create all possible combinations
        self.create_powerset_files(paths)

        # sync all repos and copy repo2 as well as repo3
        self.sync_and_copy(repos, [repo2, repo3])

        def checker(t, found):
            # only t = {3-1} should exist in share and bob, the others
            # should exist in alice and bob
            if set(t) == {3 - 1}:
                self.assertEqual(set(found), {1 - 1, 3 - 1})
            else:
                self.assertEqual(set(found), {2 - 1, 3 - 1})

        # check
        self.check_powerset_files(paths, checker)

    def test_copy_local(self):
        """
            test copy local
            procedure:
            1. create three repositories on the same host, hence all are connected
               share has set as files expression: '(alice - bob) + (bob - alice)'
               and strict flag set
            2. create files in all possible repository combinations
            3. sync all
            4. call copy in repository repo2 and repo3 (in this order)
            5. sync again
            6. now the distribution of the files looks like that:
               share: none
               alice: all files
               bob:   all files
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host, annex = h.create("Host"), a.create("Annex")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host, annex, path1, description="share", files="(alice - bob) + (bob - alice)", strict="true")
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host, annex, path2, description="alice")
        path3 = os.path.join(self.path, "repo_host3")
        repo3 = r.create(host, annex, path3, description="bob")

        paths = [path1, path2, path3]
        repos = [repo1, repo2, repo3]

        # assimilate
        repo1, repo2, repo3 = repos = self.assimilate_repos(repos)

        # init repos
        self.init_repos(repos)

        # create all possible combinations
        self.create_powerset_files(paths)

        # sync all repos and copy repo2 as well as repo3
        self.sync_and_copy(repos, [repo2, repo3])

        def checker(t, found):
            # all should exist in alice and bob (only)
            self.assertEqual(set(found), {2 - 1, 3 - 1})

        # check
        self.check_powerset_files(paths, checker)

    def test_copy_special_remote(self):
        """
            test copy
            procedure:
            1. create three repositories with this connections:
               alice (repo2) -> tracker (repo1), crypt (repo0) <- bob (repo3)
               tracker has set as files expression: '-'
               and strict flag set
               furthermore, crypt is a special remote
            2. create files in all possible repository combinations in repositories 1-3
            3. sync all
            4. call copy in repository repo2 and repo3 (in this order)
            5. sync again
            6. now the distribution of the files looks like that:
               share: none
               alice: all except the one which was only on bob
               bob:   all
               crypt: all
        """

        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]
        annex = a.create("Annex")
        conn12 = c.create(host2, host1, "/", alwayson="true")
        conn13 = c.create(host3, host1, "/", alwayson="true")

        # create & init
        path0 = os.path.join(self.path, "special")
        repo0 = r.create(host1, annex, "special", description="crypt")
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="tracker", files="-", strict="true")
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2, description="alice")
        path3 = os.path.join(self.path, "repo_host3")
        repo3 = r.create(host3, annex, path3, description="bob")

        paths = [path1, path2, path3]
        repos = [repo1, repo2, repo3]

        # assimilate
        repo1, repo2, repo3 = repos = self.assimilate_repos(repos)

        # init repos
        self.init_repos(repos)

        # init special remote on alice
        def f(repo):
            # change path
            repo.change_path()
            # execute 'git annex initremote $gitid type=rsync rsyncurl=${path0} encryption=none'
            cmd = ['git-annex', 'initremote', repo0.gitID(), 'type=rsync', 'rsyncurl=%s' % path0, 'encryption=none']
            repo.execute_command(cmd)

        self.apply_to_repos([repo2], f)

        # propagate changes
        self.sync([repo2, repo3])

        # enable crypt on bob
        def f(repo):
            # change path and execute 'git annex enableremote $gitid'
            repo.change_path()
            cmd = ['git-annex', 'enableremote', repo0.gitID()]
            repo.execute_command(cmd)

        self.apply_to_repos([repo3], f)

        # create all possible combinations
        self.create_powerset_files(paths)

        # sync all repos and copy repo2, repo3
        self.sync_and_copy(repos, [repo2, repo3])

        def checker(t, found):
            # only t = {3-1} should exist only on bob, the others
            # should exist on alice and bob
            if set(t) == {3 - 1}:
                self.assertEqual(set(found), {3 - 1})
            else:
                self.assertEqual(set(found), {2 - 1, 3 - 1})

        # check
        self.check_powerset_files(paths, checker)

    def test_copy_strict(self):
        """
            test copy strict
            procedure:
            1. create two repositories with this connection:
               alice (repo1) -> bob (repo2)
               with the following flags set:
               alice: files expresion = '-' and strict
            2. create file in repository alice (repo1)
            3. sync all
            4. call copy in repository alice (repo1)
            5. now the distribution of the files looks like that:
               alice: no
               bob: test
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2 = [h.create("Host%d" % i) for i in range(1, 2 + 1)]
        annex = a.create("Annex")
        conn12 = c.create(host1, host2, "/", alwayson="true")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="alice", files="-", strict="true")
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2, description="bob")
        repos = [repo1, repo2]

        # assimilate
        repo1, repo2 = repos = self.assimilate_repos(repos)

        # init repos
        self.init_repos(repos)

        # create file 'test' in repo1
        self.create_file(repo1, "test")

        # sync and copy files (call copy only for repo1)
        self.sync_and_copy(repos, [repo1])

        # only the link is left in repo1, where as the complete file is in repo2
        self.has_link(repo1, "test")
        self.has_file(repo2, "test")

    def test_copy_strict_remote(self):
        """
            test copy strict on remote
            procedure:
            1. create two repositories with this connection:
               alice (repo1) -> bob (repo2)
               with the following flags set:
               bob: files expresion = '-' and strict
            2. create file in repository bob (repo2)
            3. sync all
            4. call copy in repository alice (repo1)
            5. now the distribution of the files looks like that:
               alice: test
               bob: no
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2 = [h.create("Host%d" % i) for i in range(1, 2 + 1)]
        annex = a.create("Annex")
        conn12 = c.create(host1, host2, "/", alwayson="true")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="alice")
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2, description="bob", files="-", strict="true")
        repos = [repo1, repo2]

        # assimilate
        repo1, repo2 = repos = self.assimilate_repos(repos)

        # init repos
        self.init_repos(repos)

        # create file 'test' in repo2
        self.create_file(repo2, "test")

        # sync and copy files (call copy only for repo1)
        self.sync_and_copy(repos, [repo1])

        # only the link is left in repo2, where as the complete file is in repo1
        self.has_link(repo2, "test")
        self.has_file(repo1, "test")

    def test_copy_strict_via_connection(self):
        """
            test copy strict and working all the time on Host1
            (which connects to Host0 and Host1)
            procedure:
            1. create two repositories with this connection:
               alice (repo1) -> bob (repo2)
               with the following flags set:
               alice: files expresion = '-' and strict
            2. create file in repository alice (repo1)
            3. sync all
            4. call copy in repository alice (repo1)
            5. now the distribution of the files looks like that:
               alice: no
               bob: test
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2 = [h.create("Host%d" % i) for i in range(1, 2 + 1)]
        app.set_current_host(host1)
        annex = a.create("Annex")
        conn12 = c.create(host1, host2, self.path, alwayson="true")
        conn0 = [None, conn12]

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="alice", files="-", strict="true")
        path2 = "/repo_host2"
        repo2 = r.create(host2, annex, path2, description="bob")
        repos = [repo1, repo2]

        # assimilate
        repo1, repo2 = repos = [app.assimilate(r, c) for r, c in zip(repos, conn0)]

        # init repos
        repo1.init()
        repo2.init()

        # create file 'test' in repo1
        self.create_file_local(repo1, "test")

        # sync
        repo1.sync()
        repo2.sync()

        # copy
        repo1.copy()

        # sync
        repo1.sync()
        repo2.sync()

        # only the link is left in repo1, where as the complete file is in repo2
        self.has_link_local(repo1, "test")
        self.has_file_local(repo2, "test")

    def test_copy_change_copy(self):
        """
            test copy and propagation of changes
            procedure:
            1. create two repositories with this connection:
               alice (repo1) -> bob (repo2)
            2. create file in repository alice (repo1)
            3. sync all
            4. call copy in repository alice (repo1)
            5. now the file should be in both
            6. change the file in repository alice
            7. sync all
            8. copy again
            9. now the changed file should be in repository bob too
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2 = [h.create("Host%d" % i) for i in range(1, 2 + 1)]
        annex = a.create("Annex")
        conn12 = c.create(host1, host2, "/", alwayson="true")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="alice", direct="true")
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2, description="bob", direct="true")
        repos = [repo1, repo2]

        # assimilate
        repo1, repo2 = repos = self.assimilate_repos(repos)

        # init repos
        self.init_repos(repos)

        # create file 'test' in repo1
        self.create_file(repo1, "test")

        # sync and copy files (call copy only for repo1)
        self.sync_and_copy(repos, [repo1])

        # the file should be in both repositories
        self.has_file(repo1, "test")
        self.has_file(repo2, "test")

        # change file
        self.create_file(repo1, "test", "changed")

        # sync and copy files (call copy only for repo1)
        self.sync_and_copy(repos, [repo1])

        # the changed file should be in both repositories
        self.has_file(repo1, "test", "changed")
        self.has_file(repo2, "test", "changed")

    def test_sync_copy_missing_links(self):
        """
            test the behaviour of sync and copy when git remotes are missing
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2, host3 = [h.create("Host%d" % i) for i in range(1, 4)]
        annex = a.create("Annex")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1)
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2)

        repos = [repo1, repo2]

        # assimilate
        repo1, repo2 = repos = self.assimilate_repos(repos)

        # init repos
        self.init_repos(repos)

        # sync
        self.sync(repos)

        # create a connection host1 -> host2
        conn12 = c.create(host1, host2, "/", alwayson="true")

        # should fail, as the connection is not yet registered
        self.assertRaisesRegex(application.InterruptedException, "missing git remotes",
                               self.sync, [repo1])
        self.assertRaisesRegex(application.InterruptedException, "missing git remotes",
                               self.copy, [repo1])

        # these should work
        self.sync([repo2])
        self.copy([repo2])

        # reinit repos
        self.reinit_repos(repos)

        # now all should work again
        self.sync(repos)
        self.copy(repos)

        # create special repository on Host2
        path_s = os.path.join(self.path, "special")
        repo_s = r.create(host2, annex, "special", description="crypt")

        # now all should still work, as special repositories are ignored when syncing
        self.sync(repos)

        # however copy should fail, as the connection is not yet registered
        self.assertRaisesRegex(application.InterruptedException, "missing git remotes",
                               self.copy, [repo1])

        # this should still work
        self.copy([repo2])

        # reinit repos
        self.reinit_repos(repos)

        # shoud still fail
        self.assertRaisesRegex(application.InterruptedException, "missing git remotes",
                               self.copy, [repo1])

        # init special remote on repo1
        def f(repo):
            # change path
            repo.change_path()
            # execute 'git annex initremote $gitid type=rsync rsyncurl=${pathS} encryption=none'
            cmd = ['git-annex', 'initremote', repo_s.gitID(), 'type=rsync', 'rsyncurl=%s' % path_s, 'encryption=none']
            repo.execute_command(cmd)

        self.apply_to_repos([repo1], f)

        # now all should work again
        self.sync(repos)
        self.copy(repos)

    def test_migration(self):
        """
            test migration strategy
            procedure:
            1. create two repositories with this connection:
               alice (repo1) -> bob (repo2)
            2. create file in repository bob (repo2)
            3. sync all
            4. call copy in repository alice (repo1)
            5. sync all
            6. now the distribution of the files looks like that: both have the file
            -----
            7. strange things happen: the host names and repository descriptions change
               we need to restart the app, as some gurantees have been violated
            -----
            8. delete all remotes
            9. reinit
            10. create some files
            11. sync and copy
            12. now the files should be in both directories, if everything is still fine
        """
        # initialisation
        app = application.Application(self.path, verbose=self.verbose)
        h, a, r, c = app.hosts, app.annexes, app.repositories, app.connections
        host1, host2 = [h.create("Host%d" % i) for i in range(1, 2 + 1)]
        annex = a.create("Annex")
        conn12 = c.create(host1, host2, "/", alwayson="true")

        # create & init
        path1 = os.path.join(self.path, "repo_host1")
        repo1 = r.create(host1, annex, path1, description="alice")
        path2 = os.path.join(self.path, "repo_host2")
        repo2 = r.create(host2, annex, path2, description="bob")
        repos = [repo1, repo2]

        # assimilate
        repo1, repo2 = repos = self.assimilate_repos(repos)

        # init repos
        self.init_repos(repos)

        # create file 'test' in repo1
        self.create_file(repo1, "test")

        # sync and copy files (call copy only for repo1)
        self.sync_and_copy(repos, [repo1])

        # the file should be in both repositories
        self.has_file(repo1, "test")
        self.has_file(repo2, "test")

        # change host names
        host1._name = "NotHost1"
        host2._name = "NotHost2"

        # change descriptions
        repo1._data["description"] = "abel"
        repo2._data["description"] = "eve"

        # restart app
        for x in [h, a, r, c]:
            x.save()
        for x in [h, a, r, c]:
            x.load()

        # check some properties
        self.assertEqual(len(h.get_all()), 2)
        self.assertEqual(len(a.get_all()), 1)
        self.assertEqual(len(r.get_all()), 2)
        self.assertEqual(len(c.get_all()), 1)

        # refresh repos
        repos = r.get_all()

        # assimilate
        repos = self.assimilate_repos(repos)

        # delete all remotes
        self.apply_to_repos(repos, lambda r: r.delete_all_remotes())

        # re init repositories
        self.reinit_repos(repos)

        # create some files
        self.create_file(repo1, "test1")
        self.create_file(repo2, "test2")

        # sync and copy files
        self.sync_and_copy(repos, [repo1, repo2])

        # the files should be in both repositories
        for repo in repos:
            self.has_file(repo, "test1")
            self.has_file(repo, "test2")

        # there should be no strange remote branches left
        def remote_branch_checker(repo_):
            repo_.change_path()
            cmd = ["git", "branch", "--all"]
            output = subprocess.check_output(cmd).decode("UTF-8")
            self.assertNotIn("alice", output)
            self.assertNotIn("bob", output)

        self.apply_to_repos(repos, remote_branch_checker)


if __name__ == '__main__':
    unittest.main()
