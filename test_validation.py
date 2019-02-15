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

    def test_check_ruleset_type(self):
        self.assertRaises(TypeError, validation.check_ruleset, 'ruleset')
        self.assertRaises(TypeError, validation.check_ruleset, 12)
        self.assertRaises(TypeError, validation.check_ruleset, True)

    # number and date types must have units
    # ontology_id must have allowed terms, but no allowed values
    # limited_value must have allowed values, but no allowed terms
    # text must not have allowed values

    def test_check_ruleset(self):
        filename = "test_data/test_error_ruleset_missing_attributes.json"
        self.assertRaises(KeyError, validation.read_in_ruleset, filename)
        expected: List[str] = [
            "Error: valid units provided for field id having type as text which does not expect units",
            'Error: field crew_capacity has type as number but no valid units provided',
            "Error: No valid values should be provided to field class as being of text type",
            "Warning: ontology terms are provided for field color. "
            "Please re-consider whether it needs to change to ontology_id.",
            "Error: No valid terms provided to field Fake which is essential to be of ontology_id type",
            'Error: there is no allowed values for field Availability being of limited value type',
            "Error: No valid values should be provided to field manufacturer country as being of ontology_id type"
        ]
        filename = "test_data/test_error_ruleset.json"
        ruleset = validation.read_in_ruleset(filename)
        results = validation.check_ruleset(ruleset)
        print("RESULTS:\n")
        print(results)
        self.assertListEqual(expected, results)
        expected = []
        ruleset = validation.read_in_ruleset("sample_ruleset_v1.3.json")
        results = validation.check_ruleset(ruleset)
        print("RESULTS:\n")
        print(results)
        self.assertListEqual(expected, results)

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
            'duplicate_alias': [
                'There are more than one record having 404-T-132-4FE274A as its alias'
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
            ],
            "sample_relationship": [
                'Wrong JSON structure: relationship needs to be presented as a hash for record with '
                'alias 404-T-132-4FE274A',
                'Wrong JSON structure: two and only two keys (alias and relationshipNature) must be presented '
                'within every relationship. Affected record 404-T-132-4FE274A',
                'Wrong JSON structure: Unrecognized relationship nature random within record 404-T-132-4FE274A',
                'Wrong JSON structure: Unrecognized key used (only can be alias and relationshipNature) within one'
                ' relationship. Affected record 404-T-132-4FE274A',
                'Wrong JSON structure: Unrecognized key used (only can be alias and relationshipNature) within one'
                ' relationship. Affected record 404-T-132-4FE274A'
            ],
            "sample_relationship_2": [
                'Wrong JSON structure: sampleRelationships field must have values '
                'within an array for record with alias 502-W-133-4FE274B'
            ]
        }
        for error in expected.keys():
            filename = "test_data/usi/test_error_"+error+".json"
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
        filename = "test_data/test_error_duplicate_id.json"
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
        self.assertRaises(TypeError, validation.deal_with_errors, [12])
        self.assertRaises(TypeError, validation.deal_with_errors, [True])
        errors = ['1', '2']
        self.assertIsNone(validation.deal_with_errors(errors))
