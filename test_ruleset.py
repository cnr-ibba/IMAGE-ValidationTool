import Ruleset
import unittest
import json
import use_ontology


class TestRuleset(unittest.TestCase):

    def test_rule_field_types(self):
        self.assertRaises(TypeError, Ruleset.RuleField, "test", 12, "haha")
        self.assertRaises(TypeError, Ruleset.RuleField, -12.34, "12", "haha")
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", True)
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", "number", description=12)
        self.assertRaises(TypeError, Ruleset.RuleField, "test", "12", "number", multiple=True)
        self.assertRaises(ValueError, Ruleset.RuleField, "test", "number", "12")
        self.assertRaises(ValueError, Ruleset.RuleField, "test", "none", "mandatory")
        self.assertRaises(ValueError, Ruleset.RuleField, "test", "date", "optional", multiple="True")

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


