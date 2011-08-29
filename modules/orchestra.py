from modules.base import Automatia
import config
import util

try: import json
except: import simplejson as json

class OrchestraAutomatia(Automatia):
	"""Abstract helper module to wrap an Orchestra score.

	Use this helper to implement any item that can be directly 
	mapped to a single Orchestra score.

	Override do_magic() if you want to do more than just wrap a single 
	score (almost multiple scores should almost certainly be instead made
	multiple items in make-magic)

	"""
	score_name = None
	score_scope = 'one'
	score_target = config.default_orchestra_target
	score_args = {}
	score_timeout = None

	def do_magic(self):
		"""Execute an Orchestra score."""
		if self.score_name == None:
			raise NotImplementedError(self.module_name + '.score_name')

		self.execute_score(
			self.score_name,
			self.score_scope,
			self.score_target,
			self.score_args,
			self.score_timeout)

	@staticmethod
	def execute_score(name, scope='one',
	                  target=config.default_orchestra_target, args={},
	                  timeout=None):
		"""Execute an Orchestra score, block for completion, then return 
		the result as a (job_id, result) tuple.

		Will raise ``util.OrchestraError`` on any Orchestra failure.

		"""
		oc = util.OrchestraClient()
		job_id = oc.submit_job(name, scope, target, args)
		result = oc.wait_for_completion(job_id, timeout=timeout)

		if result['Status'] == 'OK': 
			return (job_id, result, )
		else: 
			raise util.OrchestraError(repr(result))

class OrchestraMetadataAutomatia(OrchestraAutomatia):
	'''Helper module to wrap an Orchestra score and update task metadata from the result
	'''

	# Mapping from orchestra response variables to metadata key names
	orchestra_response_map = None

	def get_variable_from_results(self, results, resultvarname):
		'''look through orchestra results and find the value keyed on resultvarname

		FIXME: THIS SHOULD BE IN util.py
		pre: results status is OK and players have completed the score
		'''
		# response looks like:
		# {u'Status': u'OK', u'Players': {u'orchestra.player.hostname.example': {u'Status': u'OK', u'Response': {u'echo': u'{"PATH": "/usr/bin:/usr/sbin:/bin:/sbin", "PWD": "/var/lib/service/player", "IFS": " \\t\\n", "ORC_foo": "bar", "ORC_fish": "heads"}'}}}} 
		assert results['Status'] == 'OK'
		for player,result in results['Players'].items():
			if result['Status'] != 'OK': continue
			for score,playerresponse in result['Response'].items():
				playerresponse = json.loads(playerresponse) # UGH. This should NOT be in here  FIXME: Move unrolling to OrchestraClient
				if playerresponse.has_key(resultvarname):
					return playerresponse[resultvarname]
		return KeyError("Variable '"+resultvarname+"' not returned by any Orchestra player")

	def do_magic(self):
		if self.orchestra_response_map == None: 
			raise NotImplementedError(str(self.module_name+'.orchestra_response_map'))
		results = self.execute_score(self.score_args)
		metadata_update = {}
		for response_var,metadata_key in self.orchestra_response_map.items():
			task_metadata_update[metadata_key] = self.get_variable_from_results(results, response_var)

		return dict(task_metadata_update=metadata_update)
