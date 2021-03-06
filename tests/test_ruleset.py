import unittest
import json
from typing import List, Dict

from image_validation import Ruleset
from image_validation import validation
from image_validation import ValidationResult


class TestRuleset(unittest.TestCase):
    def setUp(self):
        # to see all differences in assertEqual
        self.maxDiff = None

    def test_ontology_condition_types(self):
        self.assertRaises(TypeError, Ruleset.OntologyCondition, True, False, True, True)
        self.assertRaises(TypeError, Ruleset.OntologyCondition, 'term', 12, True, True)
        self.assertRaises(TypeError, Ruleset.OntologyCondition, 'term', False, 'True', True)
        self.assertRaises(TypeError, Ruleset.OntologyCondition, 'term', False, True, -12.34)

    def test_ontology_condition(self):
        filename = "test_data/ruleset_allowed_terms.json"

        # NOTE: file are supposed to exists while testing
        with open(filename) as infile:
            data = json.load(infile)

        # using RuleField to test accessing attributes
        test_rule_field = Ruleset.RuleField("test", "ontology_id", "recommended")
        test_rule_field.set_allowed_terms(data)

        terms = test_rule_field.get_allowed_terms()
        self.assertEqual(terms[0].term, "PATO_0000384")
        self.assertFalse(terms[0].include_descendant)
        self.assertTrue(terms[2].include_descendant)
        self.assertFalse(terms[2].include_self)
        self.assertTrue(terms[0].include_self)
        self.assertEqual(terms[1].iri, "http://purl.obolibrary.org/obo/PATO_0000383")
        self.assertEqual(terms[2].iri, "http://www.ebi.ac.uk/efo/EFO_0002012")
        expected_str = "Term: EFO_0002012 include descendant: True leaf only: True " \
                       "self included: False iri: http://www.ebi.ac.uk/efo/EFO_0002012"
        self.assertEqual(str(terms[2]), expected_str)

        for i, term in enumerate(terms):
            if i > 1:
                self.assertTrue(term.is_leaf_only())
            else:
                self.assertFalse(term.is_leaf_only())

        # test is_allowed
        # child_goat = use_ontology.Ontology('NCBITaxon_9925')
        # child_submitter = use_ontology.Ontology("EFO_0001741")
        for i, term in enumerate(terms):
            self.assertFalse(term.is_allowed('NCBITaxon_9925'))
            if i == 2:
                self.assertTrue(term.is_allowed('EFO_0001741'))
            else:
                self.assertFalse(term.is_allowed('EFO_0001741'))
        # intact female (PATO_0002365) is child of female (PATO_0000383), descendant allowed
        self.assertTrue(terms[1].is_allowed('PATO_0002365'))
        # intact male (PATO_0002366) is child of male (PATO_0000384), but the term dow not allow descendant
        self.assertFalse(terms[0].is_allowed('PATO_0002366'))

    def test_rule_field_types(self):
        self.assertRaises(TypeError, Ruleset.RuleField, "test", 12, "haha")
        self.assertRaises(TypeError, Ruleset.RuleField, -12.34, "12", "haha")
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", True)
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", "number", description=12)
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", "number", multiple=True)

        self.assertRaises(ValueError, Ruleset.RuleField, "test", "number", "12")
        self.assertRaises(ValueError, Ruleset.RuleField, "test", "none", "mandatory")
        self.assertRaises(ValueError, Ruleset.RuleField, "test", "date", "optional", multiple="True")
        rule_field = Ruleset.RuleField("test", "text", "mandatory")
        self.assertRaises(TypeError, rule_field.check_ontology_allowed, 12)
        self.assertRaises(TypeError, rule_field.check_ontology_allowed, True)

    def test_rule_field(self):
        rule_field_1 = Ruleset.RuleField("test", "ontology_id", "recommended")
        self.assertEqual(rule_field_1.get_required(), "recommended")
        self.assertEqual(rule_field_1.get_name(), "test")
        self.assertEqual(rule_field_1.get_multiple(), "no")
        self.assertFalse(rule_field_1.allow_multiple())
        # test set allowed values/units
        allowed_1 = ['first', 'second', 'third']
        allowed_2 = ['red', 'blue', 'yellow']
        self.assertEqual(len(rule_field_1.get_allowed_values()), 0)
        rule_field_1.set_allowed_values(allowed_1)
        self.assertEqual(len(rule_field_1.get_allowed_values()), 3)
        rule_field_1.set_allowed_units(allowed_1)
        self.assertEqual(rule_field_1.get_allowed_units()[0], "first")
        rule_field_1.set_allowed_units(allowed_2)
        self.assertEqual(rule_field_1.get_allowed_units()[2], "yellow")
        # test max 2
        rule_field_2 = Ruleset.RuleField("test", "text", "mandatory", multiple='max 2')
        self.assertEqual(rule_field_2.get_required(), "mandatory")
        self.assertEqual(rule_field_2.get_name(), "test")
        self.assertEqual(rule_field_2.get_multiple(), "max 2")
        self.assertTrue(rule_field_2.allow_multiple())

        # test check_ontology_allowed while testing more complicated set_allowed_terms
        filename = "test_data/ruleset_allowed_terms.json"

        # NOTE: file are supposed to exists while testing
        with open(filename) as infile:
            data = json.load(infile)

        rule_field_1.set_allowed_terms(data)
        # exact match, include self
        self.assertTrue(rule_field_1.check_ontology_allowed("PATO_0000384"))
        # child term
        # EFO_0001733 is no longer leaf node
        self.assertFalse(rule_field_1.check_ontology_allowed("EFO_0001733"))
        self.assertTrue(rule_field_1.check_ontology_allowed("EFO_0009737"))
        # no allowed terms set, so false
        self.assertFalse(rule_field_2.check_ontology_allowed("EFO_0002012"))
        self.assertFalse(rule_field_2.check_ontology_allowed("EFO_0001733"))

        rule_field_2.set_allowed_terms(data)
        # after setting, but include self is no
        self.assertFalse(rule_field_1.check_ontology_allowed("EFO_0002012"))
        # the child term should be allowed
        self.assertFalse(rule_field_2.check_ontology_allowed("EFO_0001733"))
        self.assertTrue(rule_field_2.check_ontology_allowed("EFO_0009737"))
        self.assertFalse(rule_field_1.check_ontology_allowed("NCBITaxon_28890"))
        self.assertFalse(rule_field_1.check_ontology_allowed("NCBITaxon_9605"))

    def test_rule_section_types(self):
        self.assertRaises(TypeError, Ruleset.RuleSection, 12)
        self.assertRaises(TypeError, Ruleset.RuleSection, -12.34)
        self.assertRaises(TypeError, Ruleset.RuleSection, True)
        rule_section = Ruleset.RuleSection('test')
        self.assertRaises(TypeError, rule_section.add_rule, "rule")

    def test_rule_section_serializer(self):
        reference = {
            'conditions': {},
            'name': 'test',
            'rule_names': {},
            'rules': {}}

        rule_section = Ruleset.RuleSection('test')
        test = json.loads(rule_section.to_json())

        self.assertEqual(reference, test)

    def test_rule_section(self):
        ruleset = validation.read_in_ruleset("test_data/test_ruleset.json")
        warships_section = ruleset.get_section_by_name('warships')
        self.assertRaises(TypeError, warships_section.add_condition, 12, 'value')
        self.assertRaises(TypeError, warships_section.add_condition, True, 'value')
        self.assertRaises(TypeError, warships_section.add_condition, 'field', -12.34)
        self.assertRaises(TypeError, warships_section.add_condition, 'field', False)

        expected_conditions = {'role': 'warship'}
        self.assertDictEqual(warships_section.get_conditions(), expected_conditions)
        self.assertRaises(ValueError, warships_section.add_condition, 'role', 'second role')
        self.assertRaises(ValueError, warships_section.add_rule, Ruleset.RuleField("weapon",
                                                                                   "limited value", 'mandatory'))

        rules = warships_section.get_rules()
        self.assertTrue('mandatory' in rules)
        self.assertTrue('weapon' in rules['mandatory'])
        rule = rules['mandatory']['weapon']
        self.assertTrue(type(rule) is Ruleset.RuleField)
        self.assertRaises(TypeError, warships_section.check_contain_rule_for_field, False)
        self.assertRaises(TypeError, warships_section.check_contain_rule_for_field, 12)
        self.assertFalse(warships_section.check_contain_rule_for_field('random'))
        self.assertTrue(warships_section.check_contain_rule_for_field('weapon'))

        # test meet condition
        filename = "test_data/test_data.json"

        # NOTE: file are supposed to exists while testing
        with open(filename) as infile:
            data = json.load(infile)

        transport_data = data[0]
        warship_data = data[1]

        self.assertRaises(TypeError, warships_section.meet_condition, 'dict')
        self.assertRaises(TypeError, warships_section.meet_condition, 12)
        self.assertRaises(KeyError, warships_section.meet_condition, transport_data['attributes'])
        self.assertFalse(warships_section.meet_condition(transport_data))
        self.assertTrue(warships_section.meet_condition(warship_data))
        standard_section = ruleset.get_section_by_name("standard")
        self.assertTrue(standard_section.meet_condition(warship_data))
        self.assertTrue(standard_section.meet_condition(transport_data))

    def test_rule_set_types(self):
        ruleset = Ruleset.RuleSet()
        self.assertRaises(TypeError, ruleset.add_rule_section, "rule section")
        self.assertRaises(TypeError, ruleset.get_section_by_name, True)
        self.assertRaises(TypeError, ruleset.get_section_by_name, 12)

    def test_rule_set(self):
        ruleset = validation.read_in_ruleset("test_data/test_ruleset.json")
        section_names = ['standard', 'warships', 'transports', 'dummy transport']
        self.assertListEqual(ruleset.get_all_section_names(), section_names)

        self.assertRaises(ValueError, ruleset.get_section_by_name, 'not existing')
        warships_section = ruleset.get_section_by_name('warships')
        self.assertEqual(warships_section.get_section_name(), "warships")
        # test add rule section
        new_section = Ruleset.RuleSection('new')
        duplicate_section = Ruleset.RuleSection('standard')
        self.assertRaises(ValueError, ruleset.add_rule_section, duplicate_section)
        ruleset.add_rule_section(new_section)
        section_names.append('new')
        self.assertListEqual(ruleset.get_all_section_names(), section_names)

        filename = "test_data/test_data.json"

        # NOTE: file are supposed to exists while testing
        with open(filename) as infile:
            data = json.load(infile)

        ruleset.validate(data[0], "id")

    def test_rule_set_serializer(self):
        ruleset = validation.read_in_ruleset("test_data/test_ruleset.json")
        # test string serialization
        self.assertIsInstance(ruleset.to_json(), str)

    def test_validate(self):
        ruleset = validation.read_in_ruleset("test_data/test_ruleset.json")
        expected_result: Dict[str, List[str]] = {
            "cardinality": [
                'Error: Multiple values supplied for field passenger_capacity which does not allow multiple values '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: Mandatory field crew_capacity has empty value (standard section) for Record 404-T-132-4FE274A',
                'Error: Maximum of 2 values allowed for field color but 3 values provided (standard section)'
                ' for Record 404-T-132-4FE274A',
                'Warning: recommended field manufacturer country has empty value, '
                'better remove the field (standard section) for Record 502-W-133-4FE274B',
                "{'Pass': 0, 'Warning': 1, 'Error': 1}"
            ],
            "units": [
                'Error: One of km, m need to be present for the field length '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: g for field cargo_capacity is not in the valid units list (kg) '
                '(transports section) for Record 404-T-132-4FE274A',
                'Warning: No units required but person is used as unit for field id '
                '(standard section) for Record 502-W-133-4FE274B',
                "{'Pass': 0, 'Warning': 1, 'Error': 1}"
            ],
            "values": [
                'Error: <None> of field Availability is neither "no longer available" nor a valid URI '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: <purple> of field color is not in the valid values list '
                '(<red>, <yellow>, <blue>) (standard section) for Record 502-W-133-4FE274B',
                "{'Pass': 0, 'Warning': 0, 'Error': 2}"
            ],
            "allowed_terms":[
                'Error: Invalid URI value wrong url in field manufacturer country '
                '(standard section) for Record 404-T-132-4FE274A',
                'Warning: Ontology provided for field role however there is no requirement in the ruleset '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: Not valid ontology term PATO_0000383 in field manufacturer country'
                ' (standard section) for Record 502-W-133-4FE274B',
                "{'Pass': 0, 'Warning': 0, 'Error': 2}"
            ],
            "extra_and_missing_field":[
                'Error: Mandatory field passenger_capacity in standard section could not be found '
                'for Record 404-T-132-4FE274A',
                'Warning: Column extra could not be found in ruleset for Record 502-W-133-4FE274B',
                "{'Pass': 0, 'Warning': 1, 'Error': 1}"
            ],
            "types":[
                'Error: For field crew_capacity the provided value 5 is not represented as/of the expected type Number '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: For field instruction the provided value 5 is not of the expected type doi '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: Invalid URI value wrong url for field video demo '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: The date value 15-07-2408 does not match to the format YYYY-MM-DD '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: No url found for the field manufacturer country which has the type of ontology_id '
                '(standard section) for Record 404-T-132-4FE274A',
                'Error: Invalid DOI value supplied in the field instruction '
                '(standard section) for Record 502-W-133-4FE274B',
                'Error: One of YYYY-MM-DD, YYYY-MM need to be present for the field production date '
                '(standard section) for Record 502-W-133-4FE274B',
                'Warning: Provided iri http://wrong.iri.com/obo/NCIT_C17233 does not match '
                'the iri retrieved from OLS in the field manufacturer country '
                '(standard section) for Record 502-W-133-4FE274B',

                "{'Pass': 0, 'Warning': 0, 'Error': 2}"
            ],
            "types2":[
                'Error: Email address must have prefix "mailto:" in the field video demo '
                '(standard section) for Record 404-T-132-4FE274A',
                'Warning: Provided value United kingdom has different letter case to the term '
                'referenced by http://purl.obolibrary.org/obo/NCIT_C17233 (standard section) '
                'for Record 404-T-132-4FE274A',
                'Error: mailto must be at position 1 to be a valid email value in the field video demo '
                '(standard section) for Record 502-W-133-4FE274B',
                'Error: Provided value United Kingdom does not match to the provided ontology '
                'http://purl.obolibrary.org/obo/NCIT_C16699 (standard section) for Record '
                '502-W-133-4FE274B',
                "{'Pass': 0, 'Warning': 0, 'Error': 2}"
            ]
        }
        self.maxDiff = None
        for error_type in expected_result.keys():
            filename = "test_data/data/test_error_rule_" + error_type + ".json"

            # NOTE: file are supposed to exists while testing
            with open(filename) as infile:
                data = json.load(infile)

            submission_result: List[ValidationResult.ValidationResultRecord] = []
            actual_values: List[str] = []
            for record in data:
                record_result = ruleset.validate(record, "id")
                if record_result.is_empty():
                    record_result.add_validation_result_column(
                        ValidationResult.ValidationResultColumn("Pass", "", record_result.record_id, ""))
                submission_result.append(record_result)
                for msg in record_result.get_messages():
                    actual_values.append(msg)
            summary, vcr_summary, vcr_details = \
                validation.deal_with_validation_results(submission_result, verbose=False)
            summary_str = str(summary)
            actual_values.append(summary_str)
            self.assertListEqual(expected_result[error_type], actual_values)


if __name__ == '__main__':
    unittest.main()
