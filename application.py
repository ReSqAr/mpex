import structure

#
# check python version
#
import sys
if sys.version_info<(3,2,0):
        raise RuntimeError("Python version >= 3.2 is needed.")




class Application:
	def __init__(self, path):
		# save option
		self.path = path
		
		# initialise hosts
		self.hosts = structure.Hosts(self)
		# initialise annexes
		self.annexes = structure.Annexes(self)
		# initialise host<->annex configuration
		self.repos = structure.Repositories(self)
		
		
