#!/usr/bin/python3

import os
import json
import logging

import image_validation
from image_validation import validation

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s\t%(levelname)s:\t%(name)s line %(lineno)s\t%(message)s', level=logging.INFO)

# read JSON into memory
logger.info("START")

basedir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(basedir, 'submission_example.json')

try:
    with open(filename) as infile:
        data = json.load(infile)
except FileNotFoundError:
    logger.critical("Could not find the file " + filename)
    exit(1)
except json.decoder.JSONDecodeError as e:
    logger.critical("The provided file " + filename + " is not a valid JSON file. Reason: " + str(e))
    exit(1)

data = data['sample']
usi_result = validation.check_usi_structure(data)
validation.deal_with_errors(usi_result)

dup_result = validation.check_duplicates(data)
validation.deal_with_errors(dup_result)

# read metadata rules
moduledir = image_validation.__path__[0]
rules = validation.read_in_ruleset(
    os.path.join(moduledir, "sample_ruleset_v1.3.json"))

logger.info("All sample records have unique data source ids")
ruleset_result = validation.check_with_ruleset(data, rules)
validation.deal_with_validation_results(ruleset_result)

logging.info("FINISH")
