import os
import json


class State(dict):
    """Encapsulate state common to the unit for republishing to relations."""
    def __init__(self, state_file):
        super(State, self).__init__()
        self._state_file = state_file
        self.load()

    def load(self):
        '''Load stored state from local disk.'''
        state = {}
        if os.path.exists(self._state_file):
            data = open(self._state_file, 'r').read()
            if data:
                state = json.loads(data)
        self.clear()

        self.update(state)

    def save(self):
        '''Store state to local disk.'''
        state = {}
        state.update(self)
        json.dump(state, open(self._state_file, 'wb'), indent=2)
