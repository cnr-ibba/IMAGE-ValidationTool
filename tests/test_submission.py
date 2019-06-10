import unittest
from typing import List

from image_validation import Submission, static_parameters


class TestRuleset(unittest.TestCase):
    def test_constructor(self):
        submission = Submission.Submission("notitle")
        self.assertEqual(submission.title, "notitle")
        self.assertDictEqual(submission.validation_results, dict())
        self.assertIsNone(submission.data)
        self.assertFalse(submission.data_ready_flag)
        self.assertIsNone(submission.ruleset)
        self.assertFalse(submission.ruleset_pass_flag)
        self.assertNotEqual(submission.id_field, "id")

    def test_get_title(self):
        submission = Submission.Submission("get_title")
        self.assertEqual(submission.get_title(), "get_title")
        self.assertNotEqual(submission.get_title(), "Get_title")

    def test_is_data_ready(self):
        submission = Submission.Submission("test")
        self.assertFalse(submission.is_data_ready())

    def test_is_ruleset_ready(self):
        submission = Submission.Submission("test")
        self.assertFalse(submission.is_ruleset_ready())

    def test_load_data(self):
        submission = Submission.Submission("test", id_field='id')
        submission.load_data("test_data/usi/test_error_duplicate_alias.json")
        self.assertFalse(submission.is_data_ready())
        submission.load_data("test_data/data/test_error_rule_types.json")
        self.assertTrue(submission.is_data_ready())
        # general errors generated during loading data
        load_data_result = submission.load_data("test_data/usi/file_no_existing.json")
        expected_data_file_not_found: List[str] = ['Could not find the file test_data/usi/file_no_existing.json']
        self.assertListEqual(load_data_result.get_messages(), expected_data_file_not_found)

        load_data_result = submission.load_data("test_data/test_empty.json")
        expected_data_empty_content: List[str] = [
            'The provided file test_data/test_empty.json is not a valid JSON file.'
        ]
        self.assertListEqual(load_data_result.get_messages(), expected_data_empty_content)

        load_data_result = submission.load_data("test_data/usi/test_error_duplicate_alias.json")
        expected_data: List[str] = ['There are more than one record having 404-T-132-4FE274A as its alias']
        self.assertListEqual(load_data_result.get_messages(), expected_data)

        load_data_result = submission.load_data("test_data/test_error_duplicate_id.json")
        expected_data_duplicated: List[str] = ['There are more than one record having 404-T-132-4FE274A as its id']
        self.assertListEqual(load_data_result.get_messages(), expected_data_duplicated)

        load_data_result = submission.load_data("test_data/data/test_error_rule_types.json")
        self.assertListEqual(load_data_result.get_messages(), list())

    def test_load_ruleset(self):
        submission = Submission.Submission("test")
        submission.ruleset_pass_flag = True
        self.assertTrue(submission.is_ruleset_ready())
        submission.load_ruleset("test_data/test_error_ruleset.json")
        self.assertFalse(submission.is_ruleset_ready())
        submission.load_ruleset("test_data/test_ruleset.json")
        self.assertTrue(submission.is_ruleset_ready())

        # general errors generated during loading ruleset
        load_ruleset_result = submission.load_ruleset("test_data/test_error_ruleset_missing_attributes.json")
        expected_ruleset: List[str] = ["'Each rule must have at least four attributes: Name, Type, "
                                       "Required and Allow Multiple.'"]
        self.assertListEqual(load_ruleset_result.get_messages(), expected_ruleset)
        load_ruleset_result = submission.load_ruleset("test_data/test_ruleset.json")
        self.assertListEqual(load_ruleset_result.get_messages(), list())

    # more intuitive to test those two method together
    def test_validate_and_get_validation_results(self):
        submission = Submission.Submission("test")
        # useless tests, for 100% coverage
        submission.validate()
        submission.data_ready_flag = True
        submission.validate()
        # use example data, the fake spaceship data could not do context validation
        submission.load_data("test_data/submission_example.json", section="sample")
        submission.load_ruleset(static_parameters.ruleset_filename)
        submission.validate()
        print(submission.get_validation_results())

