'''modules for use in unit testing'''

from modules.base import Automatia, CannotAutomateException
from modules.orchestra import OrchestraAutomatia, OrchestraMetadataAutomatia

class TestModule(Automatia):
	'''Test item automation model
	Successfuly automates a specific item
	'''
	can_handle = ('TestModuleItem',)

	def do_magic(self):
		return  # Returning nothing is fine. The item will still succeed

class TestModuleUnimplemented(Automatia):
	'''Test item automation model

	Raises NotImplementedError when mudpuppy tries to call do_magic
	'''
	can_handle = ('TestUnimplementedModuleItem',)

class TestAlwaysAutomates(Automatia):
	'''Test item that always automates anything it sees
	also adds stuff to both the task metadata and the state metadata
	'''
	@classmethod
	def can_automate_item(cls, item_state, task_metadata):
		return True

	def do_magic(self):
		itemstuff = { 'guess what': ['TestAlwaysAutomates was here', {'fish': 'are cool'}], 'foo': 'bar' }
		taskstuff = { 'TestAlwaysAutomates last touched': self.item_state['name'] }
		return dict( task_metadata_update=taskstuff, item_metadata_update=itemstuff )

class TestFakeIP(Automatia):
	'''Test item automation model to add task metadata
	Adds a dummy IP address to the task metadata
	'''
	can_handle = ('TestFakeIPitem',)

	def do_magic(self):
		return dict( task_metadata_update={'ip': '10.0.0.1'} )

class TestCannotAutomate(Automatia):
	can_handle = ('TestCannotAutomate item',)
	def do_magic(self):
		nyan = "NYAN NYAN NYAN NYAN NYAN NYAN NYAN NYAN NYAN"
		raise CannotAutomateException(nyan)

class TestOrchestraBad(OrchestraAutomatia):
	can_handle = ('TestOrchestraBadItem',)

class TestOrchestra(OrchestraAutomatia):
	can_handle = ('TestOrchestraItem',)
	score_name = 'helloworld'

class TestOrchestraMetadata(OrchestraMetadataAutomatia):
	can_handle = ('TestOrchestraMetadataItem',)

	# echo score returns score args passed with ORC_ prepended to the key names
	score_name = 'echo' 

	# get return variables from orchestra and put into into task metadata keys
	orchestra_response_map = { 'ORC_fish': "fish", "ORC_foo": "taskfoo" }
	score_args = { 'fish':'heads', 'foo':'bar' }
