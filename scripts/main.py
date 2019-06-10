#!/usr/bin/python3
"""
This serves as a demonstration script to showcase how to use the validation tool
1. load data
2. load ruleset
3. validate
4. process the validation result
Therefore all messages to be printed should be within this script and the actual logics are in classes
"""
import os
import logging

from image_validation import static_parameters, Submission, validation


logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s\t%(levelname)s:\t%(name)s line %(lineno)s\t%(message)s',
    level=logging.INFO)

logger.info("START")
submission = Submission.Submission("test")

# a-la django style
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
filename = os.path.join(basedir, 'test_data/submission_example.json')
load_data_results = submission.load_data(filename, section='sample')
if not submission.is_data_ready():
    logger.info("There are some issues while loading the data")
    for error in load_data_results.get_messages():
        logger.error(error)
    exit(1)

load_ruleset_results = submission.load_ruleset(static_parameters.ruleset_filename)
if not submission.is_ruleset_ready():
    logger.info("There are some issues while loading the ruleset")
    for error in load_ruleset_results.get_messages():
        logger.error(error)
    exit(1)

submission.validate()

summary, vrc_summary, vrc_detail = validation.deal_with_validation_results(submission.get_validation_results())
logger.info("Summary of records validation result")
logger.info(str(summary))
logger.info("Validation result details:")
for vrc in vrc_summary.keys():
    logger.info(f"{vrc.get_comparable_str()}   {vrc_summary[vrc]}   {str(vrc_detail[vrc])}")


logging.info("FINISH")
