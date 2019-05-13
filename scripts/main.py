#!/usr/bin/python3

import os
import json
import logging
import requests
from typing import List, Dict

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
# the data needs to be scanned twice, first time to validate individual record
# second time to validate anything involving with more than one record e.g. relationships and context validation
# first scan
# meanwhile split data according to material type for relationship checking
data_by_material: Dict[str, Dict[str, Dict]] = {}
for record in data:
    logger.info("Validate record " + record['alias'])
    record_result = ruleset.validate(record)
    submission_result[record['alias']] = record_result
    try:
        material = record['attributes']['Material'][0]['value'].lower()
        data_by_material.setdefault(material, {})
        data_by_material[material][record['alias']] = record
    except KeyError:
        # missing material value or wrong structure etc, already been dealt with by validate
        pass

for record in data:
    # if the record is with status Error, no more validation will be done
    if submission_result[record['alias']].get_overall_status() == "Error":
        continue
    record_result = submission_result[record['alias']]
    record_id = record['attributes']['Data source ID'][0]['value']
    # check relationship
    relationships = record.get('sampleRelationships', [])
    related: List[Dict] = []
    for relationship in relationships:
        target: str = relationship['alias']
        if target.startswith("SAM"):  # BioSamples data
            url = f"https://www.ebi.ac.uk/biosamples/samples/{target}"
            response = requests.get(url)
            status = response.status_code
            if status != 200:
                record_result.add_validation_result_column(
                    ValidationResult.ValidationResultColumn(
                        "Warning", f"Fail to retrieve record {target} from BioSamples as required in the relationship",
                        record_id, 'sampleRelationships'))
        else:
            if target not in submission_result:
                record_result.add_validation_result_column(
                    ValidationResult.ValidationResultColumn(
                        "Error", f"The alias {target} could not be found in the data",
                        record_id, 'sampleRelationships'))
            else:
                # in the current ruleset, derived from only from organism to specimen, so safe to only check organism
                if target in data_by_material['organism']:
                    related.append(dict(data_by_material['organism'][target]))

    if submission_result[record['alias']].get_overall_status() == "Error":
        continue

    record_result = validation.context_validation(record, record_result, related)

    if record_result.is_empty():
        record_result.add_validation_result_column(
            ValidationResult.ValidationResultColumn("Pass", "", record_result.record_id, ""))
    submission_result[record['alias']] = record_result
# pprint.pprint(rules)
summary, vrc_summary = validation.deal_with_validation_results(list(submission_result.values()))
logger.info("Summary of records validation result")
logger.info(str(summary))
logger.info("Validation result details:")
for vrc in vrc_summary.keys():
    logger.info(f"{vrc.get_comparable_str()}   {vrc_summary[vrc]}")

logging.info("FINISH")
