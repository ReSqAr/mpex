import unittest
import tempfile
import os.path

import application

class StructureTest(unittest.TestCase):
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
		conn12 = c.create(host1,host2,"/")
		conn13 = c.create(host1,host3,"/")
		conn23 = c.create(host2,host3,"/")
		conn21 = c.create(host2,host1,"/")
		conn32 = c.create(host3,host2,"/")
		conn12p= c.create(host1,host2,"/")
		
		self.assertEqual(conn12,conn12p)
		self.assertEqual(id(conn12),id(conn12p))

		self.assertEqual(c.getAll(),{conn12,conn13,conn23,conn21,conn32})

		self.assertRaisesRegex(AssertionError, "source", c.create, "", host2, "/")
		self.assertRaisesRegex(AssertionError, "dest", c.create, host1, "", "/")
		self.assertRaisesRegex(ValueError, "protocol", c.create, host1, host2, "xxx")

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
		annex1 = a.create("Annex1")
		conn12 = c.create(host1,host2,"/")
		
		# create & init
		repo11 = r.create(host1,annex1,os.path.join(self.path,"repo11"))
		repo11.init()
		
		self.assertTrue(os.path.isdir(os.path.join(repo11.path,".git")))
		self.assertTrue(os.path.isdir(os.path.join(repo11.path,".git/annex")))
		
		# create & init
		repo12 = r.create(host1,annex1,os.path.join(self.path,"repo12"),direct="true")
		self.assertRaisesRegex(AssertionError,"is not a git annex", repo12.setProperties)
		repo12.init()
		
		# create & init
		repo13 = r.create(host1,annex1,os.path.join(self.path,"repo13"))
		repo23 = r.create(host2,annex1,os.path.join(self.path,"repo13"))
		repo13.init()


if __name__ == '__main__':
	unittest.main()
