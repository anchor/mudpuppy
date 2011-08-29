#!/usr/bin/env python

'''constants for talking to make-magic'''

# Item states
#
# These are the same as core.bits.Item.allowed_states in make-magic

INCOMPLETE = 'INCOMPLETE'
FAILED = 'FAILED'
IN_PROGRESS = 'IN_PROGRESS'
COMPLETE = 'COMPLETE'


# Token name used for checking to see if we did a state change
# This must be the same across all agents talking to a make-magic server
#
# This is the same as in make-magic's mclient.py stub shell client
CHANGE_STATE_TOKEN = '_change_state_token'
