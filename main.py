#!/usr/bin/python3

import json
import validation
import logging
import ValidationResult
from typing import List

# logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s\t%(levelname)s:\t%(name)s line %(lineno)s\t%(message)s', level=logging.INFO)

# read JSON into memory
logger.info("START")
filename = 'submission_example.json'
# filename = 'exampleJSONfromUID.json'
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

ruleset = validation.read_in_ruleset("sample_ruleset_v1.3.json")
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
validation.deal_with_validation_results(submission_result)

logging.info("FINISH")
