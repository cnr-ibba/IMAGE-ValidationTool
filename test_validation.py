import validation
import unittest

ruleset_file = "sample_ruleset_v1.3.json"


class TestValidation(unittest.TestCase):

    def test_read_in_ruleset_type(self):
        self.assertRaises(TypeError, validation.read_in_ruleset, 12)
        self.assertRaises(TypeError, validation.read_in_ruleset, -12.34)
        self.assertRaises(TypeError, validation.read_in_ruleset, True)

    def test_read_in_ruleset(self):
        ruleset = validation.read_in_ruleset(ruleset_file)
        pass

