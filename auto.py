#!/usr/bin/env python

import config
import modules
import logging

registered_modules = []

class ModuleLoadException(Exception): pass

def import_class(absolutename):
	name = absolutename.split('.')
	assert (len(name) >= 2)
	modbase = ".".join(name[:-1])
	classname = name[-1]
	m = __import__(modbase, fromlist=[classname])
	return getattr(m,classname)

def register_module(module_name):
	m = import_class(module_name)

	if m in registered_modules:
		logging.exception("Module already registered: "+str(module_name))
		raise ModuleLoadException('Module already registered: %s' % (module_name))
	registered_modules.append(m)

def load_modules():
	'''load in all modules and register them
	returns the names of the modules loaded
	'''
	for module_name in config.installed_modules:
		module_name = 'modules.'+module_name
		logging.debug("Loading module "+module_name)
		register_module(module_name)
	return registered_modules

def get_modules_for_item(item_state, task_metadata):
	'''return the module classes to automate an item or empty list if one isn't found
	This only returns the classes, and does not instansiate them. They should not be instansiated
	until they are about to be run, as the constructor may throw an exception that must be
	caught.
	'''
	return [mod for mod in registered_modules if mod.can_automate_item(item_state,task_metadata)]

# Helper modules not for day to day use

def scan_for_mudpuppy_modules(pkgname='modules'):
	'''returns a list of Automatia subclasses in the modules directory
	Warning: this actually imports the things
	'''
	classes = set()
	import pkgutil
	import modules.base
	for pymodname in [name for _,name,_ in pkgutil.iter_modules([pkgname])]:
		try:
			if pymodname == 'test': continue
			pymod = __import__(pkgname+'.'+pymodname)
			pymod = getattr(pymod, pymodname)
			for key in dir(pymod):
				if key[:1] == '_': continue
				obj = getattr(pymod, key)
				if type(obj) == type and issubclass(obj, modules.base.Automatia):
					if len(obj.can_handle) == 0: continue  ## Abstract class
					classes.add("%s.%s" % (pymodname,key))
		except Exception, err:
			logging.error("! Error importing %s.%s: %s" % (pkgname,str(pymodname).ljust(20), err))
	return classes

def get_uninstalled_mudpuppy_modules():
	'''get a list of mudpuppy modules not listed in the config'''
	allmods = scan_for_mudpuppy_modules()
	ourmods = set(config.installed_modules)
	return allmods - ourmods
