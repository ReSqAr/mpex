import unittest
import tempfile
import os.path
import subprocess
import itertools

import application

class Test(unittest.TestCase):
	def setUp(self):
		# create temporary directory
		self.path = tempfile.mkdtemp()
	def tearDown(self):
		# erease variable
		self.path = None
	
	# available methods:
	# - assertFalse, assertTrue
	# - assertEqual
	# - assertRaises
	# - assertIn
	# - assertCountEqual
	# - assertIsNotNone
	
	def test_app_creation(self):
		app = application.Application(self.path)
		self.assertIsNotNone(app)
	
	def test_hosts_creation(self):
		""" test host creation and identity """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
	
		host1,host2,host3 = [h.create("Host%d"%i) for i in range(1,4)]
		host1p= h.create("Host1")
	
		self.assertEqual(host1,host1p)
		self.assertEqual(id(host1),id(host1p))

		self.assertEqual(h.getAll(),{host1,host2,host3})

	def test_hosts_creation_error_cases(self):
		""" test common error cases """
		
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections

		self.assertRaisesRegex(AssertionError, "empty", h.create, "")
		self.assertRaisesRegex(AssertionError, "invalid character", h.create, "ü")
		self.assertRaisesRegex(AssertionError, "white space", h.create, " ")



	def test_creation_annexes(self):
		""" test annex creation and identity """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
	
		# creation
		annex1,annex2,annex3 = [a.create("Annex%d"%i) for i in range(1,4)]
		annex1p= a.create("Annex1")
		
		# identity
		self.assertEqual(annex1,annex1p)
		self.assertEqual(id(annex1),id(annex1p))

		self.assertEqual(a.getAll(),{annex1,annex2,annex3})

	def test_creation_annexes_error_cases(self):
		""" test common error cases """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections

		self.assertRaisesRegex(AssertionError, "empty", a.create, "")
		self.assertRaisesRegex(AssertionError, "invalid character", a.create, "ü")
		self.assertRaisesRegex(AssertionError, "white space", a.create, " ")



	def test_creation_repositories(self):
		""" test creation of repositories """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host2,host3 = [h.create("Host%d"%i) for i in range(1,4)]
		annex1,annex2,annex3 = [a.create("Annex%d"%i) for i in range(1,4)]
		
		# creation
		repo11 = r.create(host1,annex1,os.path.join(self.path,"repo11"))
		repo12 = r.create(host1,annex2,os.path.join(self.path,"repo12"))
		repo13 = r.create(host1,annex3,os.path.join(self.path,"repo13"))
		repo21 = r.create(host2,annex1,os.path.join(self.path,"repo11"))
		repo22 = r.create(host2,annex2,os.path.join(self.path,"repo22"))
		repo23 = r.create(host2,annex3,os.path.join(self.path,"repo23"))
		repo33 = r.create(host3,annex3,os.path.join(self.path,"repo33"))
		repo11p= r.create(host1,annex2,os.path.join(self.path,"repo11"))
		
		# identity (equal if host and path are equal)
		self.assertEqual(repo11,repo11p)
		self.assertEqual(id(repo11),id(repo11p))

		self.assertEqual(r.getAll(),{repo11,repo12,repo13,repo22,repo33,repo23,repo21})
	
	def test_creation_repositories_error_cases(self):
		""" """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host1up = h.create("Host1"),h.create("HOST1")
		annex1 = a.create("Annex1")
		repo11 = r.create(host1,annex1,os.path.join(self.path,"repo11"))
		repo11up = r.create(host1up,annex1,os.path.join(self.path,"repo11"))
		
		# test error conditions
		# use repoxx, some paths are already taken, hence the identity map applies
		rxx = os.path.join(self.path,"repoxx")
		self.assertRaisesRegex(AssertionError, "Host", r.create,
					"",annex1,rxx)
		self.assertRaisesRegex(AssertionError, "Annex", r.create,
					host1,"",rxx)
		self.assertRaisesRegex(AssertionError, "absolute", r.create,
					host1,annex1,"tmp")
		self.assertRaisesRegex(AssertionError, "non-empty", r.create,
					host1,annex1,rxx,description="")
		self.assertRaisesRegex(AssertionError, "invalid", r.create,
					host1,annex1,rxx,description="ü")
		self.assertRaisesRegex(AssertionError, "trust has to be valid", r.create,
					host1,annex1,rxx,trust="unknown")
		
		# files cannot be checked on initialisation, so check only <repo>.files = <expr>
		self.assertRaisesRegex(ValueError, "non-closed", setattr,
					repo11,"files","'")
		self.assertRaisesRegex(ValueError, "no candidates", setattr,
					repo11,"files","Host5")
		self.assertRaisesRegex(ValueError, "too many candidates", setattr,
					repo11,"files","host1")
		self.assertRaisesRegex(ValueError, "too many '[)]'", setattr,
					repo11,"files","(())())")
		self.assertRaisesRegex(ValueError, "too many '[(]'", setattr,
					repo11,"files","(())(")
		
	def test_creation_repositories_metadata_default(self):
		""" check default values """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,annex1 = h.create("Host1"),a.create("Annex1")

		# default value
		repo = r.create(host1,annex1,os.path.join(self.path,"repo"))
		self.assertFalse(repo.direct)
		self.assertFalse(repo.strict)
		self.assertEqual(repo.trust,"semitrust")
		self.assertIsNone(repo.files)

	def test_creation_repositories_metadata_direct(self):
		""" check metadata direct member """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,annex1 = h.create("Host1"),a.create("Annex1")

		# direct
		repo = r.create(host1,annex1,os.path.join(self.path,"repo"),direct="false")
		self.assertFalse(repo.direct)
		repo.direct = True
		self.assertTrue(repo.direct)
		
		repo = r.create(host1,annex1,os.path.join(self.path,"repo"),direct="true")
		self.assertTrue(repo.direct)
		repo.direct = False
		self.assertFalse(repo.direct)

	def test_creation_repositories_metadata_strict(self):
		""" check metadata strict member """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,annex1 = h.create("Host1"),a.create("Annex1")
		
		# strict
		repo = r.create(host1,annex1,os.path.join(self.path,"repo"),strict="false")
		self.assertFalse(repo.strict)
		repo.strict = True
		self.assertTrue(repo.strict)
		
		repo = r.create(host1,annex1,os.path.join(self.path,"repo"),strict="true")
		self.assertTrue(repo.strict)
		repo.strict = False
		self.assertFalse(repo.strict)
		
	def test_creation_repositories_metadata_trust(self):
		""" check metadata trust member """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host2,annex1 = h.create("Host1"),h.create("Host2"),a.create("Annex1")
		
		# trust
		repo = r.create(host2,annex1,os.path.join(self.path,"repo"),trust="untrust")
		self.assertEqual(repo.trust,"untrust")
		repo.trust = "semitrust"
		self.assertEqual(repo.trust,"semitrust")
		
		repo = r.create(host1,annex1,os.path.join(self.path,"repo"),trust="trust")
		self.assertEqual(repo.trust,"trust")

	def test_creation_repositories_metadata_files(self):
		""" check metadata files member """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host2,annex1 = h.create("Host1"),h.create("Host2"),a.create("Annex1")
		
		# files
		repo = r.create(host2,annex1,os.path.join(self.path,"repo"))
		repo = r.create(host1,annex1,os.path.join(self.path,"repo"),files="  +Host1 ")
		self.assertEqual(repo.files,"+ Host1")
		repo.files = " (  host2 + )"
		self.assertEqual(repo.files,"(Host2 +)")
	
	
	def test_connection_creation(self):
		""" test the creation of connections """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host2,host3 = [h.create("Host%d"%i) for i in range(1,4)]

		# creation
		conn12 = c.create(host1,host2,"/abc/")
		conn13 = c.create(host1,host3,"/")
		conn23 = c.create(host2,host3,"/")
		conn21 = c.create(host2,host1,"/")
		conn32 = c.create(host3,host2,"ssh://server")
		conn12p= c.create(host1,host2,"/abc/")
		
		# identity
		self.assertEqual(conn12,conn12p)
		self.assertEqual(id(conn12),id(conn12p))

		self.assertEqual(c.getAll(),{conn12,conn13,conn23,conn21,conn32})

	def test_connection_creation_error_cases(self):
		""" test common error cases """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host2,host3 = [h.create("Host%d"%i) for i in range(1,4)]

		self.assertRaisesRegex(AssertionError, "source", c.create, "", host2, "/")
		self.assertRaisesRegex(AssertionError, "dest", c.create, host1, "", "/")
		self.assertRaisesRegex(ValueError, "protocol", c.create, host1, host2, "xxx")
	
	def test_connection_metadata_gitPath(self):
		""" test gitPath """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host2,host3 = [h.create("Host%d"%i) for i in range(1,4)]
		annex1 = a.create("Annex1")
		repo11 = r.create(host1,annex1,os.path.join(self.path,"repo"))
		repo21 = r.create(host2,annex1,os.path.join(self.path,"repo"))
		
		# create the connections
		conn12 = c.create(host1,host2,"/abc/")
		conn32 = c.create(host3,host2,"ssh://server")

		# test
		self.assertEqual(conn12.gitPath(repo21),"/abc" + self.path + "/repo")
		self.assertEqual(conn32.gitPath(repo21),"ssh://server" + os.path.join(self.path,"repo"))
		self.assertRaisesRegex(AssertionError,"Programming error",conn32.gitPath,repo11)

	def test_connection_metadata_alwayson(self):
		""" test alwaysOn """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host2,host3 = [h.create("Host%d"%i) for i in range(1,4)]

		# alwayson
		conn12 = c.create(host1,host2,"/",alwayson="false")
		self.assertFalse(conn12.alwaysOn)
		conn12.alwaysOn = True
		self.assertTrue(conn12.alwaysOn)
		
		conn13 = c.create(host1,host3,"/",alwayson="true")
		self.assertTrue(conn13.alwaysOn)
		conn13.alwaysOn = False
		self.assertFalse(conn13.alwaysOn)

	def test_connection_metadata_protocol(self):
		""" test protocol and pathData """
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		host1,host2,host3 = [h.create("Host%d"%i) for i in range(1,4)]
		
		# protocol
		conn1local = c.create(host1,host2,"/")
		self.assertEqual(conn1local.protocol(),"mount")

		# protocol and pathData
		conn1server = c.create(host1,host3,"ssh://myserver")
		self.assertEqual(conn1server.protocol(),"ssh")
		self.assertEqual(conn1server.pathData()["server"],"myserver")

	def test_relations(self):
		"""
			test Host's repositories and connections methods as well as
			Annex's repositories and Repository's connectedRepositories
			methods
		"""
		# initialisation
		app = application.Application(self.path)
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
		n = 3
		hosts = [h.create("Host%d"%i) for i in range(1,n+1)]
		annexes = [a.create("Annex%d"%i) for i in range(1,n+1)]
		
		# no connections nor repositories for any host
		for i in range(n):
			self.assertEqual( hosts[i].repositories(), set() )
			self.assertEqual( hosts[i].connections(), set() )
		# no repositories for any annex
		for i in range(n):
			self.assertEqual( annexes[i].repositories(), set() )
			
		repos = [
					[
						r.create(host,
									annex,
									os.path.join(self.path,"repo-%s-%s"%(host.name,annex.name)))
						for annex in annexes
					]
					for host in hosts
				]
		conns = [
					[
						c.create(source,dest,"/")
						for dest in hosts
						if source != dest
					]
					for source in hosts
				]

		# test relational methods
		for i in range(n):
			self.assertEqual( hosts[i].repositories(), set(repos[i]) )
			self.assertEqual( hosts[i].connections(), set(conns[i]) )
		for i in range(n):
			self.assertEqual( annexes[i].repositories(), {h_r[i] for h_r in repos} )
		for i in range(n): #host
			for j in range(n):
				d = {repos[k][j]: {conns[i][k if k < i else k-1]} for k in range(n) if k != i}
				self.assertEqual(repos[i][j].connectedRepositories(),d)

	def test_save(self):
		app = application.Application(self.path)
	
		# short cuts
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
	
		# create objects
		host1 = h.create("Host1")
		host2 = h.create("Host2")
		host3 = h.create("Host3")

		annex1 = a.create("Annex1")
		annex2 = a.create("Annex2")
		annex3 = a.create("Annex3")
		
		repo11 = r.create(host1,annex1,os.path.join(self.path,"repo11"),direct="true",strict="true")
		repo12 = r.create(host1,annex2,os.path.join(self.path,"repo12"),files="+host1",trust="untrust")
		repo13 = r.create(host1,annex3,os.path.join(self.path,"repo13"),trust="trust")

		conn12 = c.create(host1,host2,"/",alwayson="true")
		conn13 = c.create(host1,host3,"/")
		conn23 = c.create(host2,host3,"/")
		
		# save
		app.save()
		
		
		
		# restart
		app = application.Application(self.path)
	
		# short cuts
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
	

		self.assertEqual(h.getAll(),{host1,host2,host3})
		self.assertEqual(a.getAll(),{annex1,annex2,annex3})
		self.assertEqual(r.getAll(),{repo11,repo12,repo13})
		self.assertEqual(c.getAll(),{conn12,conn13,conn23})
		
		repo11 = r.get(host1,annex1,os.path.join(self.path,"repo11"))
		repo12 = r.get(host1,annex2,os.path.join(self.path,"repo12"))
		repo13 = r.get(host1,annex3,os.path.join(self.path,"repo13"))
		self.assertTrue(repo11.direct)
		self.assertTrue(repo11.strict)
		self.assertEqual(repo12.files,"+ Host1")
		self.assertEqual(repo12.trust,"untrust")
		self.assertEqual(repo13.trust,"trust")
		
		conn12 = c.get(host1,host2,"/")
		self.assertTrue(conn12.alwaysOn)
	
	def test_getHostedRepositories(self):
		app = application.Application(self.path)

		# short cuts
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
	
		# create objects
		host1 = h.create("Host1")
		host2 = h.create("Host2")

		annex1 = a.create("Annex1")
		annex2 = a.create("Annex2")
		
		repo11 = r.create(host1,annex1,os.path.join(self.path,"repo11"))
		repo21 = r.create(host2,annex1,os.path.join(self.path,"repo21"))
		repo12 = r.create(host1,annex2,os.path.join(self.path,"repo12"))
		repo22 = r.create(host2,annex2,os.path.join(self.path,"repo22"))
		
		self.assertRaisesRegex(RuntimeError, "Unable to find" , app.currentHost)
		
		app.setCurrentHost(host1)
		
		self.assertEqual(app.currentHost(), host1)
		# save all
		app.save()
		
		# restart
		app = application.Application(self.path)

		self.assertEqual(app.getHostedRepositories(),{repo11,repo12})
	
	def test_gitAnnexCapabilities(self):
		app = application.Application(self.path)
		
		capabilities = app.gitAnnexCapabilities
		self.assertIn("version",capabilities)
		self.assertIn("date",capabilities)
		self.assertIn("direct",capabilities)
		
		# the second call is from a cache
		capabilities2 = app.gitAnnexCapabilities
		self.assertEqual(capabilities,capabilities2)

	def test_repo_init(self):
		app = application.Application(self.path)
		
		# short cuts
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections

		# create objects
		host1 = h.create("Host1")
		app.setCurrentHost(host1)
		host2 = h.create("Host2")
		host3 = h.create("Host3")
		annex1 = a.create("Annex1")
		conn12 = c.create(host1,host2,"/abc/",alwayson="true")
		conn13 = c.create(host1,host3,"ssh://yeah/",alwayson="true")
		
		# create & init
		repo11 = r.create(host1,annex1,os.path.join(self.path,"repo11"),trust="untrust")
		repo11.init()
		# check properties
		self.assertTrue(bool(repo11.getAnnexUUID()))
		self.assertEqual(repo11.onDiskDirectMode(),"indirect")
		self.assertEqual(repo11.onDiskTrustLevel(),"untrust")
		
		# check disk format
		self.assertTrue(os.path.isdir(os.path.join(repo11.path,".git")))
		self.assertTrue(os.path.isdir(os.path.join(repo11.path,".git/annex")))
		
		# create & init
		repo12 = r.create(host1,annex1,os.path.join(self.path,"repo12"),direct="true",trust="trust")
		self.assertRaisesRegex(AssertionError,"is not a git annex", repo12.setProperties)
		repo12.init()
		repo12.setProperties()
		
		self.assertEqual(repo12.onDiskDirectMode(),"direct")
		self.assertEqual(repo12.onDiskTrustLevel(),"trust")

		# create & init
		repo13 = r.create(host1,annex1,os.path.join(self.path,"repo13"))
		repo23 = r.create(host2,annex1,os.path.join(self.path,"repo23"))
		repo33 = r.create(host3,annex1,os.path.join(self.path,"repo33"))
		repo13.init()
		repo13.setProperties()

		self.assertEqual(repo13.onDiskDirectMode(),"indirect")
		self.assertEqual(repo13.onDiskTrustLevel(),"semitrust")
		
		# check remotes
		self.assertIn("Host2",subprocess.check_output(["git","remote","show"]).decode("UTF8"))
		self.assertIn("Host3",subprocess.check_output(["git","remote","show"]).decode("UTF8"))
		with open(os.path.join(repo13.path,".git/config")) as fd:
			x = fd.read()
			self.assertIn("/abc" + repo23.path, x)
			self.assertIn("ssh://yeah" + repo33.path, x)
		
		# init non-empty directory
		path = os.path.join(self.path,"repo-nonempty")
		os.makedirs(path)
		with open(os.path.join(path,"test"),"wt") as fd:
			fd.write("test")
		
		repo_nonempty = r.create(host1,annex1,path)
		self.assertRaisesRegex(RuntimeError,"non-empty directory",repo_nonempty.init)
		# force creation and check disk format
		repo_nonempty.init(ignorenonempty=True)
		self.assertTrue(os.path.isdir(os.path.join(repo_nonempty.path,".git/annex")))
		
		# doing bad stuff
		conn12._path = "/abcd/"
		self.assertRaisesRegex(RuntimeError,"does not match",repo13.setProperties)
	
	def test_finalise(self):
		app = application.Application(self.path)
		
		# short cuts
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections

		# create objects
		host = h.create("Host1")
		app.setCurrentHost(host)
		annex = a.create("Annex1")
		
		# create & init
		path = os.path.join(self.path,"repo_indirect")
		repo_indirect = r.create(host,annex,path)
		repo_indirect.init()
		
		# (indirect mode)
		# create file
		f_path = os.path.join(path,"test")
		with open(f_path,"wt") as fd:
			fd.write("test")
		
		# test not commited?
		self.assertTrue(repo_indirect.hasUncommitedChanges())

		# finalise
		repo_indirect.finalise()
		
		# still there?
		with open(f_path,"rt") as fd:
			self.assertEqual(fd.read(),"test")
			
		# everything commited?
		self.assertFalse(repo_indirect.hasUncommitedChanges())
		
		# (direct mode)
		# create & init
		path = os.path.join(self.path,"repo_direct")
		repo_direct = r.create(host,annex,path)
		repo_direct.init()
		
		# create file
		f_path = os.path.join(path,"test")
		with open(f_path,"wt") as fd:
			fd.write("test")
		
		# test not commited?
		self.assertTrue(repo_direct.hasUncommitedChanges())

		# finalise
		repo_direct.finalise()
		
		# still there?
		with open(f_path,"rt") as fd:
			self.assertEqual(fd.read(),"test")
			
		# everything commited?
		self.assertFalse(repo_direct.hasUncommitedChanges())
	
	def test_sync(self):
		app = application.Application(self.path)
		
		# short cuts
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections

		# create objects
		host1 = h.create("Host1")
		host2 = h.create("Host2")
		annex = a.create("Annex")
		conn12 = c.create(host1,host2,"/",alwayson="true")
		
		# create & init
		path1 = os.path.join(self.path,"repo_host1")
		repo1 = r.create(host1,annex,path1,description="test_repo_1")
		path2 = os.path.join(self.path,"repo_host2")
		repo2 = r.create(host2,annex,path2,description="test_repo_2")
		
		app.setCurrentHost(host2)
		repo2.init()
		
		app.setCurrentHost(host1)
		repo1.init()
		
		# create file on host1
		f_path1 = os.path.join(path1,"test")
		with open(f_path1,"wt") as fd:
			fd.write("test")
		
		# sync changes on host1
		repo1.sync()
		
		# sync with unknown repo
		self.assertRaises(subprocess.CalledProcessError,repo1.sync,["yeah"])
		
		# sync changes on host2
		app.setCurrentHost(host2)
		repo2.sync()
		
		# there?
		f_path2 = os.path.join(path2,"test")
		self.assertTrue(os.path.isfile(f_path2) or os.path.islink(f_path2))
		
		# sync changes on host1
		app.setCurrentHost(host1)
		repo1.sync()
	
	def test_copy(self):
		app = application.Application(self.path)
		
		# short cuts
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections

		# create objects
		host1 = h.create("Host1")
		host2 = h.create("Host2")
		host3 = h.create("Host3")
		annex = a.create("Annex")
		conn12 = c.create(host2,host1,"/",alwayson="true")
		conn13 = c.create(host3,host1,"/",alwayson="true")
		
		# create & init
		path1 = os.path.join(self.path,"repo_host1")
		repo1 = r.create(host1,annex,path1,description="share", files="(alice - bob) + (bob - alice)", strict="true")
		path2 = os.path.join(self.path,"repo_host2")
		repo2 = r.create(host2,annex,path2,description="alice")
		path3 = os.path.join(self.path,"repo_host3")
		repo3 = r.create(host3,annex,path3,description="bob")
		
		paths = [path1,path2,path3]
		repos = [repo1,repo2,repo3]
		
		# init repos
		for repo in repos:
			app.setCurrentHost(repo.host)
			repo.init()
		
		# create all possible combinations on files
		n = 3
		for i in range(1,n+1):
			for t in itertools.combinations(range(n), i):
				name = "file_%s" % "".join(str(x+1) for x in t)
				for j in t:
					path = paths[j]
					f_path = os.path.join(path,name)
					print(f_path)
					with open(f_path,"wt") as fd:
						fd.write(name)
		
		# sync all repos
		for repo in reversed(repos):
			app.setCurrentHost(repo.host)
			repo.sync()
		
		# copy repo2 and repo3
		for repo in [repo2,repo3]:
			app.setCurrentHost(repo.host)
			repo.copy()

		# sync all repos
		for repo in reversed(repos):
			app.setCurrentHost(repo.host)
			repo.sync()

		# check
		for i in range(1,n+1):
			for t in itertools.combinations(range(n), i):
				name = "file_%s" % "".join(str(x+1) for x in t)
				found = []
				for j,path in enumerate(paths):
					f_path = os.path.join(path,name)
					if os.path.isfile(f_path):
						with open(f_path,"rt") as fd:
							self.assertEqual(fd.read(),name)
						found.append(j)
				
				#print("%s found in: %s" % (name,", ".join(str(x+1) for x in found)))
				
				if set(t) == {3-1}:
					self.assertEqual(set(found),{1-1,3-1})
				else:
					self.assertEqual(set(found),{2-1,3-1})
		
		
if __name__ == '__main__':
	unittest.main()
