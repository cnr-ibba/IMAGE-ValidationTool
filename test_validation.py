import validation
import unittest
import json
from typing import List, Dict

ruleset_file = "sample_ruleset_v1.3.json"


class TestValidation(unittest.TestCase):

    def test_read_in_ruleset_type(self):
        self.assertRaises(TypeError, validation.read_in_ruleset, 12)
        self.assertRaises(TypeError, validation.read_in_ruleset, -12.34)
        self.assertRaises(TypeError, validation.read_in_ruleset, True)
        self.assertRaises(FileNotFoundError, validation.read_in_ruleset, "random file")

    # this is carried out in test_ruleset
    def test_read_in_ruleset(self):
        pass

    def test_check_usi_structure(self):
        expected: Dict[str, List[str]] = {
            'not_array': ['Wrong JSON structure: all data need to be encapsulated in an array'],
            'not_dict': ['Wrong JSON structure: some records are not represented as hashes'],
            'no_alias': ['Wrong JSON structure: some records do not have alias which is mandatory '
                         'and used to identify record'],
            'alias_type': ['Wrong JSON structure: alias can only be a string'],
            'missing_title': ['Wrong JSON structure: no title field for record with alias as 404-T-132-4FE274A'],
            'just_alias': [
                'Wrong JSON structure: no title field for record with alias as 404-T-132-4FE274A',
                'Wrong JSON structure: no releaseDate field for record with alias as 404-T-132-4FE274A',
                'Wrong JSON structure: no taxonId field for record with alias as 404-T-132-4FE274A'
            ],
            "no_attributes": ['Wrong JSON structure: no attributes for record with alias as 404-T-132-4FE274A'],
            "string_taxonId": ['Wrong JSON structure: taxonId value for record 404-T-132-4FE274A is not an integer'],
            "release_date": [
                'Wrong JSON structure: The date value 2404-01 does not match to the format YYYY-MM-DD '
                'for record with alias value 404-T-132-4FE274A'
            ],
            "array_attributes": ['Wrong JSON structure: attributes must be stored as a map for record '
                                 'with alias 404-T-132-4FE274A'],
            "value_not_array": [
                'Wrong JSON structure: the values for attribute '
                'passenger_capacity needs to be in an array for record 404-T-132-4FE274A',
                'Wrong JSON structure: the values for attribute '
                'class needs to be in an array for record 404-T-132-4FE274A'
            ],
            "attribute_value": [
                'Wrong JSON structure: the values for attribute id '
                'needs to be in an array for record 404-T-132-4FE274A',
                'Wrong JSON structure: the attribute value of crew_capacity '
                'needs to be represented as a map in record 404-T-132-4FE274A',
                "Wrong JSON structure: could not find 'value' keyword for "
                "attribute passenger_capacity in record 404-T-132-4FE274A",
                'Wrong JSON structure: ontology terms need to be stored in an array in record 404-T-132-4FE274A'
            ],
            "attribute_value_2": [
                'Wrong JSON structure: Unrecognized keyword type used in '
                'attribute cargo_capacity in record 404-T-132-4FE274A',
                'Wrong JSON structure: url not used as key for ontology term in record 404-T-132-4FE274A'
            ]
        }
        for error in expected.keys():
            filename = "test_data/test_error_"+error+".json"
            try:
                with open(filename) as infile:
                    data = json.load(infile)
            except FileNotFoundError:
                print("Could not find the file " + filename)
                exit(1)
            except json.decoder.JSONDecodeError as e:
                print("The provided file " + filename + " is not a valid JSON file. Reason: " + str(e))
                exit(1)
            results = validation.check_usi_structure(data)
            self.assertListEqual(expected[error], results)

    def test_check_duplicates(self):
        filename = "test_data/test_error_duplicates.json"
        with open(filename) as infile:
            data = json.load(infile)
        self.assertRaises(TypeError, validation.check_duplicates, data, 12)
        self.assertRaises(TypeError, validation.check_duplicates, data, True)
        expected_id = ['There are more than one record having 404-T-132-4FE274A as its id']
        self.assertListEqual(validation.check_duplicates(data, "id"), expected_id)
        expected_random = ['At least one record does not have "random" field, maybe wrong case letter'
                           ' used, please double check']
        self.assertListEqual(validation.check_duplicates(data, 'random'), expected_random)

    # doing nothing, just to increase coverage
    def dummy_coverage(self):
        errors = ['']
        validation.deal_with_errors(errors)
