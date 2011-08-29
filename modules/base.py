class CannotAutomateException(Exception):
	'''signal from an Automatia that we can't automate this item
	This is NOT an error. It's just saying that the item cannot
	be processed by this module.

	This should ONLY be raised if the system state was not changed
	by the module.
	'''

class Automatia(object):
	'''Base class for anything that can automate an item'''
	can_handle = []

	def __init__(self, item_state, task_metadata):
		self.item_state = item_state
		self.task_metadata = task_metadata

	module_name = property(lambda self: self.__class__.__name__)

	@classmethod
	def can_automate_item(cls, item_state, task_metadata):
		'''return if this module can automate an item given item state and task metadata

		default implementation to return True iff item name is in
		cls.can_handle

		This must be a class method as modules can count on
		only being instantiated if they are going to be used
		to attempt to automate something
		'''
		return item_state['name'] in cls.can_handle

	def do_magic(self):
		'''automate a build step'''
		raise NotImplementedError(self.module_name+'.do_magic()')
