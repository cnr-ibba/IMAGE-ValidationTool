
import os

from . import use_ontology


ruleset_filename = os.path.join(
    os.path.dirname(use_ontology.__file__),
    "sample_ruleset_v1.5.json")

ontology_library = use_ontology.OntologyCache()
