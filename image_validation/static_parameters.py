"""
static objects used across the application
"""
import os

from . import use_ontology

# ruleset file
ruleset_filename = os.path.join(
    os.path.dirname(use_ontology.__file__),
    "sample_ruleset_v3a0ee76.json")

# ontology cache
ontology_library = use_ontology.OntologyCache()
