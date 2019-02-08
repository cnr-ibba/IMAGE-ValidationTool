#!/usr/bin/env python3
# -*- coding: utf-8 -*

import unittest
import datetime

from image_validation import misc


class TestMisc(unittest.TestCase):

    def test_get_today(self):
        dt = '2019-01-21T15:17:41.179403'
        self.assertEqual(str(dt)[:10], '2019-01-21')
        today = str(datetime.datetime.now().isoformat())
        self.assertEqual(len(dt), len(today))
        self.assertEqual(str(today)[:10], misc.get_today())

    def test_to_lower_camel_case(self):
        self.assertEqual(misc.to_lower_camel_case('country'),'country')
        self.assertEqual(misc.to_lower_camel_case('Disease'),'disease')
        self.assertEqual(misc.to_lower_camel_case('Physiological status'),'physiologicalStatus')
        self.assertEqual(misc.to_lower_camel_case('test__string'),'testString')
        self.assertEqual(misc.to_lower_camel_case('test _1'),'test1')

    def test_to_lower_camel_case_types(self):
        self.assertRaises(TypeError, misc.to_lower_camel_case, 34)
        self.assertRaises(TypeError, misc.to_lower_camel_case, True)

    def test_from_lower_camel_case(self):
        self.assertEqual(misc.from_lower_camel_case('country'), 'country')
        self.assertEqual(misc.from_lower_camel_case('disease'), 'disease')
        self.assertEqual(misc.from_lower_camel_case('physiologicalStatus'), 'physiological status')
        self.assertEqual(misc.from_lower_camel_case('testString'), 'test string')
        self.assertEqual(misc.from_lower_camel_case('test1'), 'test1')

    def test_from_lower_camel_case_types(self):
        self.assertRaises(TypeError, misc.from_lower_camel_case, 34)
        self.assertRaises(TypeError, misc.from_lower_camel_case, True)

    def test_is_email(self):
        self.assertTrue(misc.is_email("IMAGE-DCC@ebi.ac.uk"))
        # email on its own
        self.assertTrue(misc.is_email("info@a.com"))
        self.assertTrue(misc.is_email("info@a.com", only=True))
        # email with prefix mailto: which is IMAGE ruleset expects
        self.assertTrue(misc.is_email("mailto:info@a.net"))
        self.assertFalse(misc.is_email("mailto:info@a.net", only=True))
        # wrong prefix, not a valid email anymore
        self.assertFalse(misc.is_email("mail:info@a.net"))
        # wrong prefix, but still a valid email
        self.assertTrue(misc.is_email("mailtoinfo@a.co.uk"))
        self.assertTrue(misc.is_email("mailtoinfo@a.co.uk", only=True))
        # wrong prefix, not meeting IMAGE standard
        self.assertFalse(misc.is_email("mail:info@a.net", only=True))
        # space not allowed
        self.assertFalse(misc.is_email("space not allowed@a.org"))
        self.assertFalse(misc.is_email("space not allowed@a.org", only=True))
        # not a URI
        self.assertFalse(misc.is_email('EFO_0001741'))

    def test_is_email_types(self):
        self.assertRaises(TypeError, misc.is_email, 34)
        self.assertRaises(TypeError, misc.is_email, -12.34)
        self.assertRaises(TypeError, misc.is_email, True)

    def test_is_uri(self):
        self.assertTrue(misc.is_uri("www.google.com"))
        self.assertTrue(misc.is_uri("http://www.google.com"))
        self.assertTrue(misc.is_uri("mailto:somebody@google.com"))
        self.assertTrue(misc.is_uri("somebody@google.com"))
        self.assertTrue(misc.is_uri("www.url-with-querystring.com/?url=has-querystring"))
        self.assertFalse(misc.is_uri("www.  url-with-querystring.com /?url=has-querystring"))

    def test_is_uri_types(self):
        self.assertRaises(TypeError, misc.is_uri, 34)
        self.assertRaises(TypeError, misc.is_uri, -12.34)
        self.assertRaises(TypeError, misc.is_uri, True)

    def test_is_doi(self):
        # not URI
        self.assertFalse(misc.is_doi("www.google.com"))
        self.assertFalse(misc.is_doi("http://www.google.com"))
        # only prefix and suffix separated by /
        self.assertFalse(misc.is_doi("doi:10.1000"))
        self.assertFalse(misc.is_doi("doi:10.1000/one/two"))
        self.assertTrue(misc.is_doi("doi:10.1000/abc"))
        # begin with 10.
        self.assertFalse(misc.is_doi("doi:11.1000/correct"))
        # 2nd part in prefix must be no less than 1000
        self.assertFalse(misc.is_doi("doi:10.900/correct"))
        # only period used as separator
        self.assertFalse(misc.is_doi("doi:10.1000,1/correct"))
        # The registrant code may be further divided into sub-elements, assuming only one level down
        self.assertFalse(misc.is_doi("doi:10.1000.01.10/ISSN-903785736958"))

        self.assertTrue(misc.is_doi("doi:10.1000/abc"))
        self.assertTrue(misc.is_doi("doi:10.1000.01/abc-jiorhb"))
        self.assertTrue(misc.is_doi("doi:10.1000/ISSN-903785736958"))

    def test_is_doi_types(self):
        self.assertRaises(TypeError, misc.is_doi, 34)
        self.assertRaises(TypeError, misc.is_doi, -12.34)
        self.assertRaises(TypeError, misc.is_doi, True)

    def test_get_matched_date_format(self):
        self.assertEqual(misc.get_matched_date("2012-09-07", "YYYY-MM-DD"), "")
        self.assertEqual(misc.get_matched_date("2012-09", "YYYY-MM"), "")
        self.assertEqual(misc.get_matched_date("2012", "YYYY"), "")
        self.assertEqual(misc.get_matched_date( "2012-09-ab", "YYYY-MM-DD"), "Unrecognized date value 2012-09-ab")
        self.assertEqual(misc.get_matched_date("2012", "YYYY-MM"),
                         'The date value 2012 does not match to the format YYYY-MM')
        self.assertEqual(misc.get_matched_date("2012-09-07", "YYYY-MM"),
                         'The date value 2012-09-07 does not match to the format YYYY-MM')
        self.assertEqual(misc.get_matched_date("20-1-09", "YYYY-MM"),
                         'The date value 20-1-09 does not match to the format YYYY-MM')
        self.assertEqual(misc.get_matched_date("09-07-2012", "YYYY-MM-DD"),
                         'The date value 09-07-2012 does not match to the format YYYY-MM-DD')

    def test_get_matched_date_types(self):
        self.assertRaises(TypeError, misc.get_matched_date, 34, 34)
        self.assertRaises(TypeError, misc.get_matched_date, -12.34, "haha")
        self.assertRaises(TypeError, misc.get_matched_date, "ccc", True)

    def test_extract_ontology_id_from_iri(self):
        self.assertEqual(misc.extract_ontology_id_from_iri('http://www.ebi.ac.uk/efo/EFO_0001741'), "EFO_0001741")
        self.assertEqual(misc.extract_ontology_id_from_iri('http://purl.obolibrary.org/obo/NCIT_C54269'), "NCIT_C54269")
        self.assertEqual(misc.extract_ontology_id_from_iri('EFO_0001741'), "EFO_0001741")

    def test_extract_ontology_id_from_iri_types(self):
        self.assertRaises(TypeError, misc.extract_ontology_id_from_iri, 34)
        self.assertRaises(TypeError, misc.extract_ontology_id_from_iri, -12.34)
        self.assertRaises(TypeError, misc.extract_ontology_id_from_iri, True)
