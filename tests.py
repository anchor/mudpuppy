#!/usr/bin/env python

import unittest2 as unittest
import config
import auto
import sys
import util
from modules.base import CannotAutomateException

import magiclink
import constants

import logging
logging.basicConfig(level=logging.DEBUG)

'''tests for mudpuppy'''

class OrchestraTests(unittest.TestCase):
	def test_orchestra_client(self):
		oc = util.OrchestraClient()
		jobid = oc.submit_job('madworld','one',config.default_orchestra_target)
		status = oc.wait_for_completion(jobid)
		self.assertEquals(status['Status'], 'FAIL')
		jobid = oc.submit_job('helloworld','one',config.default_orchestra_target)
		status = oc.wait_for_completion(jobid)
		self.assertEquals(status['Status'], 'OK')

class ModuleTests(unittest.TestCase):
	def setUp(self):
		reload(auto)
	def tearDown(self):
		reload(auto)
	def test_1_load_modules(self):
		config.installed_modules = ('test.TestModule', )
		modules = auto.load_modules()
		self.assertEquals(len(modules),1)

		# Shouldn't allow duplication of loads
		self.assertRaises(auto.ModuleLoadException, auto.load_modules)
	def test_allocation_modules(self):
		config.installed_modules = ('test.TestModule', )
		modules = auto.load_modules()
		
		_itemdata = {'name': 'FakeItem'}
		bots = auto.get_modules_for_item(_itemdata,{})
		self.assertEquals(bots, [])

		_itemdata = {'name': 'TestModuleItem'}
		bots = auto.get_modules_for_item(_itemdata,{})
		for botclass in bots:
			self.assertIsNotNone(botclass)
			bot = botclass(_itemdata,{})
			self.assertEquals(bot.module_name, 'TestModule')
	def test_question_modules(self):
		config.installed_modules = ('test.TestFakeIP', )
		modules = auto.load_modules()
		_item_state = {'name': 'TestFakeIPitem'}
		bots = auto.get_modules_for_item(_item_state,{})
		for botclass in bots:
			bot = botclass(_item_state,{})
			self.assertIsNotNone(bot)
			self.assertEquals(bot.module_name, 'TestFakeIP')
			self.assertEquals(bot.do_magic(), {'task_metadata_update': {'ip': '10.0.0.1'}})
	def test_module_generated_cannot_automate(self):
		config.installed_modules = ('test.TestCannotAutomate', )
		modules = auto.load_modules()
		_item_state = {'name': 'TestCannotAutomateItem'}
		bots = auto.get_modules_for_item(_item_state,{})
		for botclass in bots:
			self.assertIsNotNone(botclass)
			bot = botclass(_item_state, {})
			self.assertRaises(CannotAutomateException, bot.do_magic)

class MagicAPITests(unittest.TestCase):
	def test_000_get_tasks(self):
		api = magiclink.MagicAPI()
		tasks = api.get_tasks()
		self.assertIsInstance(tasks, list)
	def test_create_delete_tasks(self):
		api = magiclink.MagicAPI()
		taskdata = api.create_task(dict(requirements=[], description="UNITTEST EPHEMERAL TEST TASK", automate=False))
		uuid = taskdata['metadata']['uuid']
		tasks = api.get_tasks()
		self.assertIn(uuid,tasks)
		api.delete_task(uuid)
		tasks = api.get_tasks()
		self.assertNotIn(uuid,tasks)

class MagicLinkTests(unittest.TestCase):
	def test_state_changes(self):
		api = magiclink.MagicLink()
		taskdata = api.create_task(dict(requirements=[], description="UNITTEST EPHEMERAL TEST TASK", automate=False))
		uuid = taskdata['metadata']['uuid']
		tasks = api.get_tasks()
		self.assertIn(uuid,tasks)

		avail = api.get_available_items(uuid)
		itemname = avail[0]['name']

		self.assertGreater(len(avail), 0)
		self.assertEqual(api.get_item_state(uuid,itemname),constants.INCOMPLETE)
		success = api.update_item_state(uuid, itemname, constants.INCOMPLETE, constants.IN_PROGRESS)
		self.assertTrue(success)
		self.assertEqual(api.get_item_state(uuid,itemname),constants.IN_PROGRESS)

		success = api.update_item_state(uuid, itemname, constants.IN_PROGRESS, constants.COMPLETE)
		self.assertTrue(success)
		self.assertEqual(api.get_item_state(uuid,itemname),constants.COMPLETE)
		avail = api.get_available_items(uuid)
		self.assertNotEqual(avail[0]['name'],itemname)

		api.delete_task(uuid)
		tasks = api.get_tasks()
		self.assertNotIn(uuid,tasks)
		
if __name__ == "__main__":
	unittest.main()
