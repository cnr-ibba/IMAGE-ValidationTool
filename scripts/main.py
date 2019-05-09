#!/usr/bin/python3

import os
import json
import logging

from typing import Dict

from image_validation import validation, ValidationResult, static_parameters

logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s\t%(levelname)s:\t%(name)s line %(lineno)s\t%(message)s',
    level=logging.INFO)

# read JSON into memory
logger.info("START")

# a-la django style
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
filename = os.path.join(basedir, 'test_data/submission_example.json')

try:
    with open(filename) as infile:
        data = json.load(infile)

except FileNotFoundError:
    logger.critical("Could not find the file " + filename)
    exit(1)

except json.decoder.JSONDecodeError as e:
    logger.critical(
        "The provided file " +
        filename +
        " is not a valid JSON file. Reason: " +
        str(e))
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
    logger.error("Found errors in check_ruleset!")

logger.info("Loaded the ruleset")
submission_result: Dict[str, ValidationResult.ValidationResultRecord] = {}
for record in data:
    logger.info("Validate record " + record['alias'])
    record_result = ruleset.validate(record)
    record_result = validation.context_validation(
        record, record_result)
    if record_result.is_empty():
        record_result.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                    "Pass", "", record_result.record_id, ""))
    submission_result[record['alias']] = record_result
# pprint.pprint(rules)
summary, vrc_summary = validation.deal_with_validation_results(list(submission_result.values()))
logger.info(str(summary))
for vrc in vrc_summary.keys():
    logger.info(f"{vrc.get_comparable_str()}   {vrc_summary[vrc]}")

logging.info("FINISH")
