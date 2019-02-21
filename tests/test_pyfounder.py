import unittest

import pyfounder


class PyfounderTestCase(unittest.TestCase):

    def setUp(self):
        self.app = pyfounder.app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        self.assertIn('Welcome to pyfounder', rv.data.decode())


if __name__ == '__main__':
    unittest.main()
