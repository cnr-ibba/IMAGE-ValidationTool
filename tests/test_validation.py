import unittest
import json
from typing import List, Dict

from image_validation import validation
from image_validation import static_parameters
from image_validation import ValidationResult


class TestValidation(unittest.TestCase):
    def setUp(self):
        # to see all differences in assertEqual
        self.maxDiff = None

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
            'Error: Valid units provided for field id having type as text which does not expect units',
            'Error: Field crew_capacity has type as number but no valid units provided',
            'Error: No valid values should be provided to field class as being of text type',
            'Error: No valid terms provided to field Fake which is essential to be of ontology_id type',
            'Error: There is no allowed values for field Availability being of limited value type',
            'Error: No valid values should be provided to field manufacturer country as being of ontology_id type',
            'Warning: Ontology terms are provided for field color. '
            'Please re-consider whether it needs to change to ontology_id type.'
        ]
        filename = "test_data/test_error_ruleset.json"
        ruleset = validation.read_in_ruleset(filename)
        results = validation.check_ruleset(ruleset)
        self.assertListEqual(expected, results.get_messages())
        print("here")
        print(results.get_messages())
        expected = []
        ruleset = validation.read_in_ruleset(static_parameters.ruleset_filename)
        results = validation.check_ruleset(ruleset)
        self.assertListEqual(expected, results.get_messages())

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
                'Wrong JSON structure: two and only two keys (alias/accession and relationshipNature) must be presented '
                'within every relationship. Affected record 404-T-132-4FE274A',
                'Wrong JSON structure: Unrecognized relationship nature random within record 404-T-132-4FE274A',
                'Wrong JSON structure: Unrecognized key used (only can be alias/accession and relationshipNature) '
                'within one relationship. Affected record 404-T-132-4FE274A',
                'Wrong JSON structure: Unrecognized key used (only can be alias/accession and relationshipNature) '
                'within one relationship. Affected record 404-T-132-4FE274A'
            ],
            "sample_relationship_2": [
                'Wrong JSON structure: More than one relationship natures found within record 404-T-132-4FE274A',
                'Duplicated relationship same as with 502-W-133-4FE274B for record 504-Y-133-25ED74B',
                'Duplicated relationship derived from with 502-W-133-4FE274B for record 504-Y-133-25ED74E',
                'Wrong JSON structure: sampleRelationships field must have values '
                'within an array for record with alias 502-W-133-4FE274B'
            ],
            "sample_relationship_accession": [
                'Wrong JSON structure: In relationship accession can only take BioSamples accession, not SAMX00000001',
                'Wrong JSON structure: In relationship accession can only take BioSamples accession, '
                'not 502-W-133-4FE274B',
                'Wrong JSON structure: In relationship alias can only take non-BioSamples accession, not SAMD00000001'
            ]
        }
        data = dict()
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
            self.assertListEqual(expected[error], results.get_messages())

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
    def test_deal_with_errors(self):
        self.assertRaises(TypeError, validation.deal_with_errors, [12])
        self.assertRaises(TypeError, validation.deal_with_errors, [True])
        errors = ['dummy', 'test']
        self.assertIsNone(validation.deal_with_errors(errors))

    def test_deal_with_validation_results(self):
        submission_result = []
        error = ValidationResult.ValidationResultRecord("record 1")
        error.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                "Error", "coverage for deal with validation results", "record 1", "field"))
        submission_result.append(error)

        pass_result = ValidationResult.ValidationResultRecord("pass")
        submission_result.append(pass_result)

        error_2 = ValidationResult.ValidationResultRecord("record 2")
        error_2.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                "Error", "another error", "record 2", "field"))
        error_2.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                "Warning", "one warning", "record 2", "another field"))
        submission_result.append(error_2)

        warning = ValidationResult.ValidationResultRecord("record 3")
        warning.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                "Warning", "one warning", "record 3", "another field"))
        submission_result.append(warning)
        summary, vrc_summary, vrc_details = validation.deal_with_validation_results(submission_result, True)
        self.assertDictEqual(summary, {'Pass': 1, 'Warning': 1, 'Error': 2})
        vrc_summary_converted = dict()
        vrc_detail_converted = dict()
        for key_value in vrc_summary.keys():
            vrc_summary_converted[key_value.get_comparable_str()] = vrc_summary[key_value]
            vrc_detail_converted[key_value.get_comparable_str()] = vrc_details[key_value]
        self.assertDictEqual(vrc_summary_converted, {
            "Error: coverage for deal with validation results": 1,
            "Error: another error": 1,
            "Warning: one warning": 2
        })
        self.assertDictEqual(vrc_detail_converted,{
            "Error: coverage for deal with validation results": {'record 1'},
            "Error: another error": {"record 2"},
            "Warning: one warning": {"record 2", "record 3"}
        })

    def test_coordinate_check_type(self):
        self.assertRaises(TypeError, validation.coordinate_check, "str", ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.coordinate_check, True, ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.coordinate_check, {},
                          ValidationResult.ValidationResultColumn("Pass", "", "id", ""))
        self.assertRaises(TypeError, validation.coordinate_check, {}, "id", "")

    def test_coordinate_check(self):
        expected: List[List[str]] = [
            [],  # animal, no, missing => correct
            ['Error: No value provided for field Birth location but value in field Birth location accuracy is not '
             'missing geographic information for Record animal_42'],  # animal, no, unknown accuracy => wrong
            [],  # sample, italy, country level => correct,
            ['Error: Value Italy provided for field Collection place but value in field Collection place accuracy '
             'is missing geographic information for Record sample_257']  # sample, italy, missing => wrong
        ]
        filename = "test_data/context/test_error_context_location_accuracy.json"
        with open(filename) as infile:
            data = json.load(infile)
        data = data['sample']
        for i, record in enumerate(data):
            existing_results = ValidationResult.ValidationResultRecord(record['alias'])
            existing_results = validation.coordinate_check(record['attributes'], existing_results)
            self.assertListEqual(existing_results.get_messages(), expected[i])

    def test_animal_sample_check_type(self):
        self.assertRaises(TypeError, validation.animal_sample_check, "str", {},
                          ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.animal_sample_check, True, {},
                          ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.animal_sample_check, {}, "str",
                          ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.animal_sample_check, {}, True,
                          ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.animal_sample_check, {}, {},
                          ValidationResult.ValidationResultColumn("Pass", "", "id", "field"))
        self.assertRaises(TypeError, validation.animal_sample_check, {}, {}, "id")

    def test_animal_sample_check_and_species_check(self):
        filename = "test_data/context/test_error_context_animal_sample_relationship.json"
        with open(filename) as infile:
            data = json.load(infile)
        data = data['sample']
        cache = dict()
        for record in data:
            cache[record['alias']] = record
        results_correct = ValidationResult.ValidationResultRecord('sample_257')
        results_wrong = ValidationResult.ValidationResultRecord('sample_256')
        results_correct = validation.animal_sample_check(cache['sample_257'], cache['animal_35'], results_correct)
        results_wrong = validation.animal_sample_check(cache['sample_256'], cache['animal_35'], results_wrong)
        self.assertListEqual(results_correct.get_messages(), [])
        self.assertListEqual(results_wrong.get_messages(),
                             ['Error: The Species of sample (Bos taurus) does not match to the Species of '
                              'related animal (Sus scrofa) for Record sample_256'])

        results = validation.species_check(cache['sample_257'], results_correct)
        self.assertListEqual(results.get_messages(),
                             ['Error: taxonId 9913 does not match ontology term used in species '
                              'http://purl.obolibrary.org/obo/NCBITaxon_9823 for Record sample_257'])

        result_organism_part_error = ValidationResult.ValidationResultRecord('sample_255')
        result_organism_part_error = validation.animal_sample_check(cache['sample_255'], cache['animal_42'],
                                                              result_organism_part_error)
        self.assertListEqual(result_organism_part_error.get_messages(),
                             ['Error: Organism part (Semen) could not be taken from '
                              'a female animal for Record sample_255'])
        result_organism_part_warning = ValidationResult.ValidationResultRecord('sample_571')
        result_organism_part_warning = validation.animal_sample_check(cache['sample_571'], cache['animal_57'],
                                                              result_organism_part_warning)
        self.assertListEqual(result_organism_part_warning.get_messages(),
                             ['Warning: Organism part (Semen) is expected to be taken from a male animal, '
                              'please check the sex value (record of unknown sex) is correct for Record sample_571'])

    def test_child_of_check_type(self):
        self.assertRaises(TypeError, validation.child_of_check, "str", [],
                          ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.child_of_check, True, [],
                          ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.child_of_check, {}, "str",
                          ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.child_of_check, {}, True,
                          ValidationResult.ValidationResultRecord("id"))
        self.assertRaises(TypeError, validation.child_of_check, {}, [],
                          ValidationResult.ValidationResultColumn("Pass", "", "id", "field"))
        self.assertRaises(TypeError, validation.child_of_check, {}, [], "id")

    def test_child_of_check_and_species_breed_check(self):
        filename = "test_data/context/test_error_context_animal_child_of.json"
        with open(filename) as infile:
            data = json.load(infile)
        data = data['sample']
        cache = dict()
        for record in data:
            cache[record['alias']] = record

        results_correct = ValidationResult.ValidationResultRecord('animal_355')
        results_correct = validation.child_of_check(cache['animal_355'], [cache['animal_35']], results_correct)
        results_correct = validation.species_breed_check(cache['animal_355'], results_correct)

        results_wrong = ValidationResult.ValidationResultRecord('animal_428')
        results_wrong = validation.child_of_check(cache['animal_428'], [cache['animal_42']], results_wrong)
        results_wrong = validation.species_breed_check(cache['animal_428'], results_wrong)

        self.assertListEqual(results_correct.get_messages(),
                             ['Warning: No check has been carried out on whether Randomed pig breed is a Sus scrofa '
                              'breed as no mapped breed provided for Record animal_355'
                              ])
        self.assertListEqual(results_wrong.get_messages(),
                             ['Error: The Species of child (Bos taurus) does not match to the Species of '
                              'parent (Sus scrofa) for Record animal_428',
                              'Error: The mapped breed http://purl.obolibrary.org/obo/LBO_0000358 does not match '
                              'the given species Bos taurus for Record animal_428'
                              ])

    def test_parents_sex_check(self):
        filename = "test_data/context/test_error_context_animal_parent_sex.json"
        with open(filename) as infile:
            data = json.load(infile)
        data = data['sample']
        cache = dict()
        for record in data:
            cache[record['alias']] = record

        results_correct = ValidationResult.ValidationResultRecord('animal_428')
        related = [cache['animal_42'], cache['animal_35']]
        results_correct = validation.parents_sex_check(related, results_correct)
        self.assertListEqual(results_correct.get_messages(), [])

        results_wrong = ValidationResult.ValidationResultRecord('animal_355')
        related = [cache['animal_36'], cache['animal_35']]
        results_wrong = validation.parents_sex_check(related, results_wrong)
        self.assertListEqual(results_wrong.get_messages(),
                             ["Error: Two parents could not have same sex for Record animal_355"])

        results_unknown = ValidationResult.ValidationResultRecord('animal_555')
        related = [cache['animal_66'], cache['animal_35']]
        results_unknown = validation.parents_sex_check(related, results_unknown)
        self.assertListEqual(results_unknown.get_messages(),
                             ["Warning: At least one parent has unknown value for sex, "
                              "thus could not be checked for Record animal_555"])


    def test_context_validation(self):
        expected_results: List[List[str]] = [
            [],
            ['Error: No value provided for field Birth location but value in field Birth location accuracy is not '
             'missing geographic information for Record animal_42'],
            [],
            [],
            ['Error: The Species of child (Bos taurus) does not match to the Species '
             'of parent (Sus scrofa) for Record animal_428'],
            ['Error: The Species of sample (Bos taurus) does not match to the Species '
             'of related animal (Sus scrofa) for Record sample_256'],
            ['Error: Value Italy provided for field Collection place but value in field Collection place accuracy '
             'is missing geographic information for Record sample_257',
             'Error: taxonId 9913 does not match ontology term used in species '
             'http://purl.obolibrary.org/obo/NCBITaxon_9823 for Record sample_257'],
            ['Error: Specimen can only derive from one animal for Record sample_777'],
            ['Error: Having more than 2 parents defined in sampleRelationships for Record animal_555']
        ]
        filename = "test_data/context/test_error_context_all.json"
        with open(filename) as infile:
            data = json.load(infile)
        data = data['sample']

        cache = dict()
        for record in data:
            cache[record['alias']] = record

        for i, record in enumerate(data):
            existing_results = ValidationResult.ValidationResultRecord(record['alias'])
            related = list()
            relationships = record.get('sampleRelationships', [])
            for relationship in relationships:
                target: str = relationship['alias']
                related.append(cache[target])
            existing_results = validation.context_validation(record, existing_results, related)
            self.assertListEqual(existing_results.get_messages(), expected_results[i])

    def test_image_animal(self):
        # get image test file
        filename = "test_data/image_animal.json"

        # NOTE: file are supposed to exists while testing
        with open(filename) as infile:
            animal = json.load(infile)

        # read ruleset
        ruleset = validation.read_in_ruleset(
                static_parameters.ruleset_filename)

        # now check animal
        result = ruleset.validate(animal).get_messages()
        self.assertEqual(result, [])

    def test_image_sample(self):
        # get image test file
        filename = "test_data/image_sample.json"

        # NOTE: file are supposed to exists while testing
        with open(filename) as infile:
            sample = json.load(infile)

        # read ruleset
        ruleset = validation.read_in_ruleset(
                static_parameters.ruleset_filename)

        # now check sample
        result = ruleset.validate(sample).get_messages()
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
