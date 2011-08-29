#!/usr/bin/env python

'''A very, very simple mudpuppy implementation
'''

import os
import sys
import auto
import util
import config
import time
import traceback
import signal

from constants import *
from modules.base import CannotAutomateException
from magiclink import MagicLink

import logging
import logging.config
logging.config.fileConfig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'logging.conf'))

exit_gracefully = False

def sighup_handler(signum, frame):
	global exit_gracefully
	exit_gracefully = True
	print "got SIGHUP"
signal.signal(signal.SIGHUP, sighup_handler)


def automate_task(uuid):
	'''find an item that we can do in a task and automate it

	At the moment we return as soon as we automate a single item successfully

	returns True if we managed to automate anything
	'''	

	api = MagicLink()

	automated_something = False

	for item in api.get_available_items(uuid):
		item_name = item['name']
		if automated_something: break

		# Needs to be at least as new as the available list
		task_metadata = api.get_task_metadata(uuid)
		for module in auto.get_modules_for_item(item, task_metadata):
			if automated_something: break
			# Lock
			if not api.update_item_state(uuid, item_name, INCOMPLETE, IN_PROGRESS):
				break	# Couldn't lock item. Try the next
			logging.info('Set %s/%s to IN_PROGRESS' %(uuid,item_name))

			# Attempt to run
			try:
				builder = module(item, task_metadata)
				result = builder.do_magic()
				if result != None and result.has_key('task_metadata_update'):
					api.update_task_metadata(uuid, result['task_metadata_update'])
					logging.debug('updating task metadata for %s with: %s' %(uuid,result['task_metadata_update']))
				if result != None and result.has_key('item_metadata_update'):
					api.update_item(uuid, item_name, result['item_metadata_update'])
					logging.debug('updating item metadata for %s/%s with: %s' %(uuid,item_name,result['item_metadata_update']))
			except CannotAutomateException:
				# Unlock and try the next builder
				logging.debug('Module threw CANNOT_AUTOMATE. Continuing with other modules if there are there', exc_info=1)
				logging.info('Setting %s/%s to INCOMPLETE' %(uuid,item_name))
				worked = api.update_item_state(uuid, item_name, IN_PROGRESS, INCOMPLETE)
				if not worked:
					logging.error("Couldn't set item state from IN_PROGRESS to FAILED! Task may be in inconsistant state")
					return False
				continue
			except Exception, e:
				logging.error('Module threw an exception. Setting the item to FAILED', exc_info=1)
				worked = api.update_item_state(uuid, item_name, IN_PROGRESS, FAILED)
				if not worked:
					logging.error("Couldn't set item state from IN_PROGRESS TO FAILED! Task may be in inconsistant state")
					return False
				automated_something = True
				break

			logging.info('Module finished. Setting %s/%s to COMPLETE' %(uuid,item['name']))
			automated_something = True
			worked = api.update_item_state(uuid, item_name, IN_PROGRESS, COMPLETE)
			if not worked:
				logging.error("Couldn't set item state from IN_PROGRESS TO COMPLETE! Task may be in inconsistant state")
				return False

	return automated_something
	
def mudpuppy_main():
	logging.config.fileConfig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'logging.conf'))

	api = MagicLink()

	# Load in the modules that do the real work
	auto.load_modules()

	logging.info("Started. Waiting for things to do.")
	while not exit_gracefully:
		tasks = api.get_tasks()

		automated_something = False
		for uuid in tasks:
			automated = automate_task(uuid)		
			automated_something |= automated

		if not automated_something:
			# Didn't manage to change the state of anything
			# so wait at least a second before hammering
			# the server again
			time.sleep(1)
			continue

		logging.debug("Polling make-magic for serverbuilds for us to automate")
	logging.info("Exiting gracefully after SIGHUP")


if __name__ == '__main__':
	mudpuppy_main()
