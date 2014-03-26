import os
import cPickle as pickle


class State(dict):
    """Encapsulate state common to the unit for republishing to relations."""
    def __init__(self, state_file):
        super(State, self).__init__()
        self._state_file = state_file
        self.load()

    def load(self):
        '''Load stored state from local disk.'''
        if os.path.exists(self._state_file):
            state = pickle.load(open(self._state_file, 'rb'))
        else:
            state = {}
        self.clear()

        self.update(state)

    def save(self):
        '''Store state to local disk.'''
        state = {}
        state.update(self)
        pickle.dump(state, open(self._state_file, 'wb'))
