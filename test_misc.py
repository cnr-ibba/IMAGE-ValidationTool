# import sys
# sys.path.insert(0, '../IMAGE-ValidationTool')

import unittest
import misc


class TestMisc(unittest.TestCase):

    def test_to_lower_camel_case(self):
        self.assertEqual(misc.to_lower_camel_case('country'),'country')
        self.assertEqual(misc.to_lower_camel_case('Disease'),'disease')
        self.assertEqual(misc.to_lower_camel_case('Physiological status'),'physiologicalStatus')
        self.assertEqual(misc.to_lower_camel_case('test__string'),'testString')
        self.assertEqual(misc.to_lower_camel_case('test _1'),'test1')