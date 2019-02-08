
import unittest

from image_validation import validation


class TestValidation(unittest.TestCase):

    def test_read_in_ruleset_type(self):
        self.assertRaises(TypeError, validation.read_in_ruleset, 12)
        self.assertRaises(TypeError, validation.read_in_ruleset, -12.34)
        self.assertRaises(TypeError, validation.read_in_ruleset, True)

    def test_read_in_ruleset(self):
        pass
