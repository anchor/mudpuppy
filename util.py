#!/usr/bin/env python

import config
import socket
import auto
import json
import time
import functools
import logging

class TimeoutException(Exception): pass
class OrchestraError(Exception): pass
class OrchestraJSONError(OrchestraError): pass

def timecall(func, *args, **argd):
	start = time.time()
	try: ret = func(*args,**argd)
	finally: print time.time() - start
	return ret

def poll_until_not_none(func, delay=0.1, backoff=1, max_delay=None, timeout=None):
	'''call a function regularly until it returns not None and then return the result

	the function is called every 'delay' seconds
	after every unsuccessful call, the delay is multiplied by 'backoff', and limited to max_delay

	if timeout is set, a TimeoutException is raised if that much time has passed without result
	the function will always be called at least once without delay, regardless of the value of timeout
	if a timeout is set the function may be called immediately before timing out, even if the delay was longer
	'''
	#if timeout is not None:
	start = time.time()
	while True:
		beforecall = time.time()-start
		ret = func()
		if ret is not None: return ret
		elapsed = time.time()-start
		if timeout is not None and elapsed >= timeout:
			raise TimeoutException()
		sleepfor = delay - (elapsed-beforecall)
		if timeout is not None and elapsed+sleepfor > timeout:
			sleepfor = timeout-elapsed
		if sleepfor > 0:
			time.sleep(sleepfor)
		delay *= backoff
		if max_delay:
			delay = min(delay, max_delay)

class OrchestraClient(object):
	'''Simple Orchestra Audience

	>>> oc = OrchestraClient()
	>>> oc.submit_job('helloworld','one','orchestra.player.hostname.example')
	200034
	>>> oc.get_status(200034)
	{u'Status': u'OK', u'Players': {u'orchestra.player.hostname.example': {u'Status': u'OK', u'Response': {}}}}
	>>> oc.submit_job('madworld','one','orchestra.player.hostname.example')
	200035
	>>> oc.get_status(200035)
	{u'Status': u'FAIL', u'Players': {u'orchestra.player.hostname.example': {u'Status': u'HOST_ERROR', u'Response': {}}}}
	>>> oc.submit_job('echo','one','orchestra.player.hostname.example', {'foo': 12345, 'nyan': 54321, 'cat': 'dog'})
	200038
	>>> oc.wait_for_completion(200038, timeout=30)
	{u'Status': u'OK', u'Players': {u'orchestra.player.hostname.example': {u'Status': u'OK', u'Response': {u'echo': u'{"IFS": " \\t\\n", "ORC_nyan": "54321", "PWD": "/var/lib/service/player", "ORC_foo": "12345", "PATH": "/usr/bin:/usr/sbin:/bin:/sbin", "ORC_cat": "dog"}'}}}}
	'''
	def _get_conductor_socket(self):
		'''get a socket connected to the conductor
		current implementation is a UNIX socket'''
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sock.connect(config.orchestra_socket)
		return sock

	def orchestra_request(self, **argd):
		'''make a request to the Orchestra conductor
		pre: all non-positional arguments passed form a well-formed orchestra request
		'''
		sock = self._get_conductor_socket()
		f = sock.makefile()
		try:
			json.dump(argd, f)
			f.flush()
			data = f.read()
			response = json.loads(data)
		except ValueError:
			if data == '':
				raise OrchestraError('Conductor burned socket. Probably invalid call')
			raise OrchestraJSONError(("Couldn't decode as JSON",data))
		finally:
			sock.close()

		if response[0] == 'OK':
			# FIXME: This is not demarshalling any json coming back from individual players!
			return response[1]	
		else:
			raise OrchestraError(response[1])

	def submit_job(self, score, scope, target, args={}):
		'''submit a job to orchestra as per the Audience API
		Any keys and values in args will be coerced into unicode objects
		'''
		if isinstance(target, basestring):
			target = [target]
		args = dict((unicode(k),unicode(v)) for k,v in args.items())
		request = dict(Op='queue', Score=score, Scope=scope, Players=list(target), Params=args)
		logging.debug('Submitting Orchestra job: %s', repr(request))
		return self.orchestra_request(**request)

	def get_status(self, jobid):
		return self.orchestra_request(Op='status', Id=jobid)

	def completed_status_or_none(self, jobid):
		'''return the job status if completed or failed, or None if still Pending'''
		status = self.get_status(jobid)
		return None if status['Status'] == 'PENDING' else status

	def wait_for_completion(self, jobid, timeout=None, delay=0.1, backoff=1.41414, max_poll_delay=2):
		'''Block until an orchestra job leaves the Pending state
		returns the status response of the job when it is available
		raises TimeoutException iff timeout is not None and timeout seconds 
		have passed without the job leaving the Pending state

		Orchestra calls are async, so we just keep polling until we get
		somewhere
		'''
		pf = functools.partial(self.completed_status_or_none, jobid)
		return poll_until_not_none(pf, delay=delay, backoff=backoff, timeout=timeout, max_delay=max_poll_delay)
