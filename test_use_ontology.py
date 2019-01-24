import use_ontology
import unittest

class TestUseOntology(unittest.TestCase):

    # this test is more about how to use zooma properly, the function itself is like a by-product
    def test_use_ontology(self):
        # category: species
        # organism in gxa datasource with high, disallow any datasource, good
        expected = {
            'type': 'organism',
            'confidence': 'High',
            'text': 'Mus musculus',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/NCBITaxon_10090'
        }
        self.assertDictEqual(use_ontology.use_zooma('mus musculus', 'species'), expected)
        self.assertDictEqual(use_ontology.use_zooma('mus musculus', 'organism'), expected)
        self.assertIs(use_ontology.use_zooma('mouse', 'organism'), None)
        # category: country
        expected = {
            'type': 'country',
            'confidence': 'Good',
            'text': 'Germany',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/NCIT_C16636'
        }
        # country type=null, two matches medium/low, so returned value is None
        self.assertDictEqual(use_ontology.use_zooma('germany', 'country'), expected)
        self.assertIs(use_ontology.use_zooma('deutschland', 'country'), None)
        # country type=null, while using ena datasource, high
        test = use_ontology.use_zooma('norway','country')
        if not test:
            print ("\nIMAGE zooma library not loaded into Zooma for mapping")
        # category: breed
        expected = {
            'type': 'breed',
            'confidence': 'Good',
            'text': 'Bentheim Black Pied',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/LBO_0000347'
        }
        self.assertDictEqual(use_ontology.use_zooma('bentheim black pied','breed'), expected)
        # category: other
        # Health status	type=disease
        expected = {
            'type': 'disease',
            'confidence': 'High',
            'text': 'normal',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/PATO_0000461'
        }
        self.assertDictEqual(use_ontology.use_zooma('normal', 'disease'), expected)
        # Organism part
        expected = {
            'type': 'organism part',
            'confidence': 'High',
            'text': 'spleen',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/UBERON_0002106'
        }
        self.assertDictEqual(use_ontology.use_zooma('spleen', 'organism part'), expected)
        # Organism part UBERON_0001968 (semen) medium for default OLS setting
        self.assertIs(use_ontology.use_zooma('semen', 'organism part'), None)
        # developmental stage
        expected = {
            'type': 'developmental stage',
            'confidence': 'High',
            'text': 'adult',
            'ontologyTerms': 'http://www.ebi.ac.uk/efo/EFO_0001272'
        }
        self.assertDictEqual(use_ontology.use_zooma('adult','developmental stage'), expected)

        # Physiological stage several medium/low none of them related to physiological stage PATO_0001701 (mature)
        self.assertIs(use_ontology.use_zooma('mature','physiological stage'), None)
        # test limiting datasource
        # without limiting to LBO, match to a random GAZ term
        self.assertIs(use_ontology.use_zooma('Poitevine', 'breed'), None)
        # without mapping to the country
        self.assertIsNone(use_ontology.use_zooma('turkey', 'species'))

    def test_use_ontology_types(self):
        self.assertRaises(TypeError, use_ontology.use_zooma, 'string', 123)
        self.assertRaises(TypeError, use_ontology.use_zooma, -12.34, 'string')
        self.assertRaises(TypeError, use_ontology.use_zooma, False, 'string')

    def test_get_general_breed_by_species(self):
        expected_goat = {
            'text': 'goat breed',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/LBO_0000954'

        }
        self.assertDictEqual(use_ontology.get_general_breed_by_species('capra HIrcus'), expected_goat)
        expect_pig_cross = {
            'text': 'Pig crossbreed',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/LBO_0001040'

        }
        self.assertDictEqual(use_ontology.get_general_breed_by_species('sus scrofa', True), expect_pig_cross)
        self.assertIs(use_ontology.get_general_breed_by_species('random species'), None)

    def test_get_general_breed_by_species_types(self):
        self.assertRaises(TypeError, use_ontology.get_general_breed_by_species, 123)
        self.assertRaises(TypeError, use_ontology.get_general_breed_by_species, -12.34)
        self.assertRaises(TypeError, use_ontology.get_general_breed_by_species, False)
        self.assertRaises(TypeError, use_ontology.get_general_breed_by_species, 'string', 'False')
        self.assertRaises(TypeError, use_ontology.get_general_breed_by_species, 'string', 0)
        self.assertRaises(TypeError, use_ontology.get_general_breed_by_species, 'string', -1.0)

    # the asserted values are subject to change
    def test_ontology(self):
        wrong = use_ontology.Ontology("WRONG")
        self.assertFalse(wrong.found)
        self.assertEqual(wrong.get_short_term(), "WRONG")
        self.assertEqual(wrong.get_iri(), "")
        self.assertEqual(wrong.get_label(), "")
        self.assertListEqual(wrong.get_labels_and_synonyms(), [])
        self.assertEqual(wrong.get_ontology_name(), '')
        self.assertIsNone(wrong.is_leaf())

        correct_human = use_ontology.Ontology('NCBITaxon_9606')
        self.assertTrue(correct_human.found)
        self.assertEqual(correct_human.get_short_term(), "NCBITaxon_9606")
        self.assertEqual(correct_human.get_iri(), "http://purl.obolibrary.org/obo/NCBITaxon_9606")
        self.assertEqual(correct_human.get_label(), "Homo sapiens")
        expected = ['Homo sapiens']
        self.assertListEqual(correct_human.get_labels_and_synonyms(), expected)
        self.assertEqual(correct_human.get_ontology_name(), 'ncbitaxon')
        self.assertFalse(correct_human.is_leaf())

        correct_submitter = use_ontology.Ontology("EFO_0001741")
        self.assertTrue(correct_submitter.found)
        self.assertEqual(correct_submitter.get_short_term(), "EFO_0001741")
        self.assertEqual(correct_submitter.get_iri(), "http://www.ebi.ac.uk/efo/EFO_0001741")
        self.assertEqual(correct_submitter.get_label(), "submitter")
        expected = ['submitter']
        self.assertListEqual(correct_submitter.get_labels_and_synonyms(), expected)
        self.assertEqual(correct_submitter.get_ontology_name(), 'efo')
        self.assertTrue(correct_submitter.is_leaf())

        correct_hair = use_ontology.Ontology("UBERON_0001037")
        self.assertTrue(correct_hair.found)
        self.assertEqual(correct_hair.get_short_term(), "UBERON_0001037")
        self.assertEqual(correct_hair.get_iri(), "http://purl.obolibrary.org/obo/UBERON_0001037")
        self.assertEqual(correct_hair.get_label(), "strand of hair")
        expected = ['strand of hair', 'hair']
        self.assertListEqual(correct_hair.get_labels_and_synonyms(), expected)
        self.assertEqual(correct_hair.get_ontology_name(), 'uberon')
        self.assertFalse(correct_hair.is_leaf())

        self.assertFalse(correct_hair.label_match_ontology("strand Hair"))
        self.assertFalse(correct_hair.label_match_ontology("strand of Hair"))
        self.assertFalse(correct_hair.label_match_ontology("Hair"))
        self.assertTrue(correct_hair.label_match_ontology("Hair", False))

        self.assertFalse(correct_hair.__eq__(correct_human))
        self.assertTrue(correct_hair == correct_hair)

        self.assertRaises(TypeError, use_ontology.Ontology, 12)
        self.assertRaises(TypeError, use_ontology.Ontology, -12.34)
        self.assertRaises(TypeError, use_ontology.Ontology, True)

        self.assertRaises(TypeError, correct_hair.label_match_ontology, "string", "true")
        self.assertRaises(TypeError, correct_hair.label_match_ontology, "string", 1)
        self.assertRaises(TypeError, correct_hair.label_match_ontology, "string", -1.0)
        self.assertRaises(TypeError, correct_hair.label_match_ontology, 12, True)
        self.assertRaises(TypeError, correct_hair.label_match_ontology, 12.34, True)
        self.assertRaises(TypeError, correct_hair.label_match_ontology, True, True)

    def test_ontology_cache(self):
        short_term  = "NCBITaxon_9606"
        ontology = use_ontology.Ontology(short_term)
        # test contains and add_ontology
        cache = use_ontology.OntologyCache()
        self.assertFalse(cache.contains(short_term))
        cache.add_ontology(ontology)
        self.assertTrue(cache.contains(short_term))
        # test get_ontology
        retrieved = cache.get_ontology(short_term)
        self.assertEqual(ontology, retrieved)
        # test has_parent
        self.assertTrue(cache.has_parent(short_term, "NCBITaxon_1"))
        # wrong direction
        self.assertFalse(cache.has_parent("NCBITaxon_1", short_term))
        # irrelevant
        self.assertFalse(cache.has_parent("UBERON_0001037", "EFO_0001741"))

        self.assertRaises(TypeError, cache.add_ontology, "string")
        self.assertRaises(TypeError, cache.add_ontology, 12)
        self.assertRaises(TypeError, cache.get_ontology, 12)
        self.assertRaises(TypeError, cache.get_ontology, True)
        self.assertRaises(TypeError, cache.has_parent, "str", True)
        self.assertRaises(TypeError, cache.has_parent, True, "str")


