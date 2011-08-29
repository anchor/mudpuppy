#!/usr/bin/env python

mudpuppy_api_url = 'http://localhost:4554/'

orchestra_socket = '/var/run/conductor.sock'
default_orchestra_target = 'localhost' # see modules.orchestra

installed_modules = (
		'test.TestAlwaysAutomates',
	)

try:
	from localconfig import *
except:
	pass
