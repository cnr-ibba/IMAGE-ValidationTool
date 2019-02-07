import Ruleset
import validation
import unittest
import json


class TestRuleset(unittest.TestCase):

    def test_ontology_condition_types(self):
        self.assertRaises(TypeError, Ruleset.OntologyCondition, True, False, True, True)
        self.assertRaises(TypeError, Ruleset.OntologyCondition, 'term', 12, True, True)
        self.assertRaises(TypeError, Ruleset.OntologyCondition, 'term', False, 'True', True)
        self.assertRaises(TypeError, Ruleset.OntologyCondition, 'term', False, True, -12.34)
        self.assertRaises(TypeError, Ruleset.OntologyCondition, 'True', False, True, True, True)

    def test_ontology_condition(self):
        filename = "test_data/ruleset_allowed_terms.json"
        try:
            with open(filename) as infile:
                data = json.load(infile)
        except FileNotFoundError:
            exit(1)
        except json.decoder.JSONDecodeError as e:
            exit(1)

        # using RuleField to test accessing attributes
        test_rule_field = Ruleset.RuleField("test", "ontology_id", "recommended")
        test_rule_field.set_allowed_terms(data)

        terms = test_rule_field.get_allowed_terms()
        self.assertEqual(terms[0].term, "PATO_0000384")
        self.assertFalse(terms[1].include_descendant)
        self.assertTrue(terms[2].include_descendant)
        self.assertFalse(terms[2].include_self)
        self.assertTrue(terms[1].include_self)
        self.assertEqual(terms[1].iri, "http://purl.obolibrary.org/obo/PATO_0000383")
        self.assertEqual(terms[2].iri, "http://www.ebi.ac.uk/efo/EFO_0002012")

        for i, term in enumerate(terms):
            if i == 3:
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

    def test_rule_field_types(self):
        self.assertRaises(TypeError, Ruleset.RuleField, "test", 12, "haha")
        self.assertRaises(TypeError, Ruleset.RuleField, -12.34, "12", "haha")
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", True)
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", "number", description=12)
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", "number", multiple=True)

        self.assertRaises(ValueError, Ruleset.RuleField, "test", "number", "12")
        self.assertRaises(ValueError, Ruleset.RuleField, "test", "none", "mandatory")
        self.assertRaises(ValueError, Ruleset.RuleField, "test", "date", "optional", multiple="True")

    def test_rule_field(self):
        rule_field_1 = Ruleset.RuleField("test", "ontology_id", "recommended")
        self.assertEqual(rule_field_1.get_required(), "recommended")
        self.assertEqual(rule_field_1.get_name(), "test")
        self.assertEqual(rule_field_1.get_multiple(), "no")
        self.assertFalse(rule_field_1.allow_multiple())
        rule_field_2 = Ruleset.RuleField("test", "text", "mandatory", multiple='max 2')
        self.assertEqual(rule_field_2.get_required(), "mandatory")
        self.assertEqual(rule_field_2.get_name(), "test")
        self.assertEqual(rule_field_2.get_multiple(), "max 2")
        self.assertTrue(rule_field_2.allow_multiple())

        # test check_ontology_allowed while testing more complicated set_allowed_terms
        filename = "test_data/ruleset_allowed_terms.json"
        try:
            with open(filename) as infile:
                data = json.load(infile)
        except FileNotFoundError:
            exit(1)
        except json.decoder.JSONDecodeError as e:
            exit(1)

        rule_field_1.set_allowed_terms(data)
        # exact match, include self
        self.assertTrue(rule_field_1.check_ontology_allowed("PATO_0000383"))
        # child term
        self.assertTrue(rule_field_1.check_ontology_allowed("EFO_0001733"))
        # no allowed terms set, so false
        self.assertFalse(rule_field_2.check_ontology_allowed("EFO_0002012"))
        self.assertFalse(rule_field_2.check_ontology_allowed("EFO_0001733"))
        rule_field_2.set_allowed_terms(data)
        # after setting, but include self is no
        self.assertFalse(rule_field_1.check_ontology_allowed("EFO_0002012"))
        # the child term should be allowed
        self.assertTrue(rule_field_2.check_ontology_allowed("EFO_0001733"))
        self.assertFalse(rule_field_1.check_ontology_allowed("NCBITaxon_9913"))

    def test_rule_section_types(self):
        self.assertRaises(TypeError, Ruleset.RuleSection, 12)
        self.assertRaises(TypeError, Ruleset.RuleSection, -12.34)
        self.assertRaises(TypeError, Ruleset.RuleSection, True)

        self.assertRaises(TypeError, Ruleset.RuleSection.add_rule, "rule")

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
        try:
            with open(filename) as infile:
                data = json.load(infile)
        except FileNotFoundError:
            exit(1)
        except json.decoder.JSONDecodeError as e:
            exit(1)
        transport_data = data[0]
        warship_data = data[1]
        self.assertFalse(warships_section.meet_condition(transport_data))
        self.assertTrue(warships_section.meet_condition(warship_data))
        standard_section = ruleset.get_section_by_name("standard")
        self.assertTrue(standard_section.meet_condition(warship_data))
        self.assertTrue(standard_section.meet_condition(transport_data))

    def test_rule_set_types(self):
        self.assertRaises(TypeError, Ruleset.RuleSet.add_rule_section, "rule section")
        self.assertRaises(TypeError, Ruleset.RuleSet.get_section_by_name, True)
        self.assertRaises(TypeError, Ruleset.RuleSet.get_section_by_name, 12)

    def test_rule_set(self):
        ruleset = validation.read_in_ruleset("test_data/test_ruleset.json")
        section_names = ['standard', 'warships', 'transports']
        self.assertListEqual(ruleset.get_all_section_names(), section_names)
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
        try:
            with open(filename) as infile:
                data = json.load(infile)
        except FileNotFoundError:
            exit(1)
        except json.decoder.JSONDecodeError as e:
            exit(1)
        ruleset.validate(data[0], "id")

