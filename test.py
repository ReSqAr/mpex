import unittest
import tempfile
import os.path
import subprocess

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
	
	def test_object_creation(self):
		app = application.Application(self.path)
	
		# short cuts
		h,a,r,c = app.hosts,app.annexes,app.repositories,app.connections
	
		#
		# test hosts
		#
		host1 = h.create("Host1")
		host2 = h.create("Host2")
		host3 = h.create("Host3")
		host1p= h.create("Host1")
		
		self.assertEqual(host1,host1p)
		self.assertEqual(id(host1),id(host1p))

		self.assertEqual(h.getAll(),{host1,host2,host3})

		self.assertRaisesRegex(AssertionError, "empty", h.create, "")
		self.assertRaisesRegex(AssertionError, "invalid character", h.create, "ü")
		self.assertRaisesRegex(AssertionError, "white space", h.create, " ")
		

		#
		# test annexes
		#
		annex1 = a.create("Annex1")
		annex2 = a.create("Annex2")
		annex3 = a.create("Annex3")
		annex1p= a.create("Annex1")
		
		self.assertEqual(annex1,annex1p)
		self.assertEqual(id(annex1),id(annex1p))

		self.assertEqual(a.getAll(),{annex1,annex2,annex3})

		self.assertRaisesRegex(AssertionError, "empty", a.create, "")
		self.assertRaisesRegex(AssertionError, "invalid character", a.create, "ü")
		self.assertRaisesRegex(AssertionError, "white space", a.create, " ")
	
		#
		# test repositories
		#
		repo11 = r.create(host1,annex1,os.path.join(self.path,"repo11"))
		repo12 = r.create(host1,annex2,os.path.join(self.path,"repo12"))
		repo13 = r.create(host1,annex3,os.path.join(self.path,"repo13"))
		repo22 = r.create(host2,annex2,os.path.join(self.path,"repo22"))
		repo23 = r.create(host2,annex3,os.path.join(self.path,"repo23"))
		repo33 = r.create(host3,annex3,os.path.join(self.path,"repo33"))
		repo11p= r.create(host1,annex2,os.path.join(self.path,"repo11"))
		
		# equal if host and path are equal
		self.assertEqual(repo11,repo11p)
		self.assertEqual(id(repo11),id(repo11p))

		self.assertEqual(r.getAll(),{repo11,repo12,repo13,repo22,repo33,repo23})
		
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
		self.assertRaisesRegex(ValueError, "non-closed", r.create,
					host1,annex1,rxx,files="'")
		self.assertRaisesRegex(ValueError, "no candidates", r.create,
					host1,annex1,rxx,files="Host5")
		host1pp = h.create("HOST1")
		self.assertRaisesRegex(ValueError, "too many candidates", r.create,
					host1,annex1,rxx,files="host1")
		self.assertRaisesRegex(ValueError, "too many '[)]'", r.create,
					host1,annex1,rxx,files="(())())")
		self.assertRaisesRegex(ValueError, "too many '[(]'", r.create,
					host1,annex1,rxx,files="(())(")
		
		# test truthful representation of the input data
		# default value
		repo110 = r.create(host1,annex1,os.path.join(self.path,"repo110"))
		self.assertFalse(repo110.direct)
		self.assertFalse(repo110.strict)
		self.assertEqual(repo110.trust,"semitrust")
		self.assertIsNone(repo110.files)
		
		# direct
		repo111 = r.create(host1,annex1,os.path.join(self.path,"repo111"),direct="false")
		self.assertFalse(repo111.direct)
		repo111.direct = True
		self.assertTrue(repo111.direct)
		
		repo112 = r.create(host1,annex1,os.path.join(self.path,"repo112"),direct="true")
		self.assertTrue(repo112.direct)
		repo112.direct = False
		self.assertFalse(repo112.direct)
		
		# strict
		repo113 = r.create(host1,annex1,os.path.join(self.path,"repo113"),strict="false")
		self.assertFalse(repo113.strict)
		repo113.strict = True
		self.assertTrue(repo113.strict)
		
		repo114 = r.create(host1,annex1,os.path.join(self.path,"repo114"),strict="true")
		self.assertTrue(repo114.strict)
		repo114.strict = False
		self.assertFalse(repo114.strict)
		
		# trust
		repo115 = r.create(host1,annex1,os.path.join(self.path,"repo115"),trust="untrust")
		self.assertEqual(repo115.trust,"untrust")
		repo115.trust = "semitrust"
		self.assertEqual(repo115.trust,"semitrust")
		
		repo116 = r.create(host1,annex1,os.path.join(self.path,"repo116"),trust="trust")
		self.assertEqual(repo116.trust,"trust")
		
		# files
		repo117 = r.create(host1,annex1,os.path.join(self.path,"repo117"),files="  +Host1 ")
		self.assertEqual(repo117.files,"+ Host1")
		repo117.files = " (  host2 + )"
		self.assertEqual(repo117.files,"(Host2 +)")
		
		#
		# test connections
		#
		conn12 = c.create(host1,host2,"/abc/")
		conn13 = c.create(host1,host3,"/")
		conn23 = c.create(host2,host3,"/")
		conn21 = c.create(host2,host1,"/")
		conn32 = c.create(host3,host2,"ssh://server")
		conn12p= c.create(host1,host2,"/abc/")
		
		self.assertEqual(conn12,conn12p)
		self.assertEqual(id(conn12),id(conn12p))

		self.assertEqual(c.getAll(),{conn12,conn13,conn23,conn21,conn32})

		self.assertRaisesRegex(AssertionError, "source", c.create, "", host2, "/")
		self.assertRaisesRegex(AssertionError, "dest", c.create, host1, "", "/")
		self.assertRaisesRegex(ValueError, "protocol", c.create, host1, host2, "xxx")
		self.assertRaises(AssertionError,conn12.gitPath,repo11)
		
		self.assertEqual(conn12.gitPath(repo22),"/abc" + self.path + "/repo22")
		self.assertEqual(conn32.gitPath(repo22),"ssh://server" + os.path.join(self.path,"repo22"))
		
		# always on
		hostx = h.create("HostX")
		conn1x = c.create(host1,hostx,"/",alwayson="false")
		self.assertFalse(conn1x.alwaysOn)
		conn1x.alwaysOn = True
		self.assertTrue(conn1x.alwaysOn)
		
		hosty = h.create("HostY")
		conn1y = c.create(host1,hosty,"/",alwayson="true")
		self.assertTrue(conn1y.alwaysOn)
		conn1y.alwaysOn = False
		self.assertFalse(conn1y.alwaysOn)
		
		# protocol
		hostlocal = h.create("HostLocal")
		conn1local = c.create(host1,hostlocal,"/")
		self.assertEqual(conn1local.protocol(),"mount")

		hostserver = h.create("HostServer")
		conn1server = c.create(host1,hostserver,"ssh://server")
		self.assertEqual(conn1server.protocol(),"ssh")
		
		# test relational methods
		self.assertEqual(host2.repositories(), {repo22,repo23})
		self.assertEqual(host2.connections(), {conn23,conn21})
		self.assertEqual(annex3.repositories(), {repo13,repo23,repo33})
		self.assertEqual(repo33.connectedRepositories(),{repo23:{conn32}})

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
		repo12 = r.create(host1,annex2,os.path.join(self.path,"repo12"),files="+host3",trust="untrust")
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
		self.assertEqual(repo12.files,"+ Host3")
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
		conn12 = c.create(host1,host2,"/",alwayson="true")
		conn13 = c.create(host1,host3,"/",alwayson="true")
		
		# create & init
		path1 = os.path.join(self.path,"repo_host1")
		repo1 = r.create(host1,annex,path1,description="test_repo_1")
		path2 = os.path.join(self.path,"repo_host2")
		repo2 = r.create(host2,annex,path2,description="test_repo_2")
		path3 = os.path.join(self.path,"repo_host3")
		repo3 = r.create(host3,annex,path3,description="test_repo_3")
		
		app.setCurrentHost(host3)
		repo3.init()
		app.setCurrentHost(host2)
		repo2.init()
		app.setCurrentHost(host1)
		repo1.init()
		
		# create file on host1
		f_path1 = os.path.join(path1,"test")
		with open(f_path1,"wt") as fd:
			fd.write("test")
		# sync changes on host1
		repo1.copy()

		# create file on host1
		f2_path1 = os.path.join(path1,"test_only_in2")
		with open(f2_path1,"wt") as fd:
			fd.write("test_only_in2")
		# sync changes on host1 only to host2
		repo1.copy(["test_repo_2"])

		# sync changes on host2
		app.setCurrentHost(host2)
		repo2.sync()

		# sync changes on host3
		app.setCurrentHost(host3)
		repo3.sync()
		
		# there?
		f_path2 = os.path.join(path2,"test")
		with open(f_path2,"rt") as fd:
			self.assertEqual(fd.read(),"test")
		f2_path2 = os.path.join(path2,"test_only_in2")
		with open(f2_path2,"rt") as fd:
			self.assertEqual(fd.read(),"test_only_in2")
		
		# there?
		f_path3 = os.path.join(path3,"test")
		with open(f_path3,"rt") as fd:
			self.assertEqual(fd.read(),"test")
		f2_path3 = os.path.join(path3,"test_only_in2")
		self.assertFalse(os.path.isfile(f2_path3))
			
		
		
if __name__ == '__main__':
	unittest.main()
