#!/usr/bin/env python

'''Access the make-magic HTTP API

contains both make-magic HTTP API access and the policy for dealing with the same
'''
import requests
import json
import random

from constants import *
import config

class MagicError(Exception):
        def __init__(self, error, description):
                self.response,self.content = response,content
        def __str__(self):
		return "MudpuppyError: %s: %s" %(str(self.response), str(self.content))

class MagicAPI(object):
	'''Talk to the make-magic API over HTTP
	'''
	## HTTP Specific
	#
	def json_http_request(self, method, url, decode_response = True, data=None):
		'''Make a HTTP request, and demarshal the HTTP response

		if POST is given, the data is marshalled to JSON put in the 
		HTTP request body
		'''
		assert url[:4] == 'http'
		headers = {'User-Agent': 'mudpuppy MagicAPI'}
		if method == 'POST':
			json_data = json.dumps(data)
			headers['Content-Type'] = 'application/json'
			response = requests.request(method, url, headers=headers, data=json_data)
		else:
			response = requests.request(method, url)

		if response.status_code == None: 
			# Didn't manage to get a HTTP response
			response.raise_for_status()

		if response.status_code != 200:
			# Got an error, but hopefully make-magic gave us more information
			try:
				jsondata = json.loads(response.content)
				raise MagicError(jsondata['error'], jsondata['message'])
			except:	
				# Couldn't marshal. Raise a less interesting error.
				response.raise_for_status()

		# Yay! good response. Try and marshal to JSON and return
		if decode_response:
			return json.loads(response.content)
		else:
			return response.content

	def full_url(self, relpath):
		'''return the full URL from a relative API path'''
		if config.mudpuppy_api_url[-1] == '/':
			config.mudpuppy_api_url = config.mudpuppy_api_url[:-1]
		return "%s/%s" % (config.mudpuppy_api_url,relpath)

	def json_http_get(self, relpath, decode_response=True):
		return self.json_http_request('GET', self.full_url(relpath), decode_response)
	def json_http_post(self, relpath, data, decode_response=True):
		return self.json_http_request('POST', self.full_url(relpath), decode_response, data)
	def json_http_delete(self, relpath, decode_response=True):
		return self.json_http_request('DELETE', self.full_url(relpath), decode_response)

	## API to expose
	#
	def get_tasks(self):
		'''return a list of all task UUIDs'''
		return self.json_http_get('task')
	def get_task(self,uuid):
		'''return all data for a task'''
		return self.json_http_get('task/%s' % (str(uuid),))
	def get_task_metadata(self,uuid):
		'''return metadata for a task'''
		return self.json_http_get('task/%s/metadata' % (str(uuid),))
	def update_task_metadata(self,uuid, updatedict):
		'''update metadata for a task'''
		return self.json_http_post('task/%s/metadata' % (str(uuid),),updatedict)
	def get_available_items(self,uuid):
		'''return all items in a task that are currently ready to be automated'''
		return self.json_http_get('task/%s/available' % (str(uuid),))
	def update_item(self,uuid,itemname, updatedict):
		'''update data for a specific item'''
		return self.json_http_post('task/%s/%s' % (str(uuid),str(itemname)),updatedict)
	def get_item(self,uuid,itemname):
		'''return data for a specific item'''
		return self.json_http_get('task/%s/%s' % (str(uuid),str(itemname)))
	def get_item_state(self,uuid,itemname):
		'''return item state for a specific item'''
		return self.json_http_get('task/%s/%s/state' % (str(uuid),str(itemname)),decode_response=False)
	def create_task(self,taskdatadict):
		'''create a new task
		mudpuppy shouldn't have to do this ever but it is here for
		completeness and testing.  Unless you want to automatically
		create tasks from a task, in which case, power to you.
		'''
		return self.json_http_post('task/create', taskdatadict)
	def delete_task(self,uuid):
		'''delete a task
		mudpuppy REALLY shoudn't be doing this, but is here for testing
		and completeness. Unless you want to automatically delete
		tasks from a task, in which case I'll be hiding behind this rock
		'''
		return self.json_http_delete('task/%s' % (str(uuid),))

class MagicLink(MagicAPI):
	'''wrap the make-magic API while adding some of the logic for dealing with it
	'''
	def update_item_state(self, uuid, item, old_state, new_state):
		'''atomically update the item state, failing if we don't manage to

		returns True iff the state was changed from old_state to new_state and this call made the change
		'''
		token = random.randint(1,2**48)
		item_state_update = {"state": new_state, "onlyif": dict(state=old_state)}
		item_state_update[CHANGE_STATE_TOKEN] = token

		new_item = self.update_item(uuid, item, item_state_update)
		return new_item.get('state') == new_state and new_item.get(CHANGE_STATE_TOKEN) == token
