#!/usr/bin/python3

import os
import json
import logging
import ValidationResult
import static_parameters
from typing import List

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
logger.info("All sample records have unique data source ids")

ruleset = validation.read_in_ruleset(static_parameters.ruleset_filename)
ruleset_check = validation.check_ruleset(ruleset)
if ruleset_check:
    validation.deal_with_errors(ruleset_check)
    exit()
logger.info("Loaded the ruleset")
submission_result: List[ValidationResult.ValidationResultRecord] = []
for record in data:
    logger.info("Validate record "+record['alias'])
    record_result = ruleset.validate(record)
    record_result = validation.context_validation(record['attributes'], record_result)
    if record_result.is_empty():
        record_result.add_validation_result_column(
            ValidationResult.ValidationResultColumn("Pass", "", record_result.record_id))
    submission_result.append(record_result)
# pprint.pprint(rules)
summary = validation.deal_with_validation_results(submission_result)
print(summary)

logging.info("FINISH")