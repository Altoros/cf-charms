import tempfile
import os
import unittest

from helpers.state import State


class TestState(unittest.TestCase):
    def setUp(self):
        _, fn = tempfile.mkstemp()
        self._state_file = fn

    def tearDown(self):
        if self._state_file:
            os.unlink(self._state_file)

    def test_empty(self):
        s = State(self._state_file)
        self.assertEqual(s, {})

    def test_serialization(self):
        s = State(self._state_file)
        s['foo'] = 'bar'
        s.save()
        s.load()
        self.assertEqual(s, {'foo': 'bar'})


if __name__ == '__main__':
    unittest.main()
