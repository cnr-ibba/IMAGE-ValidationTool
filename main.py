#!/usr/bin/python3

import json
import validation
import datetime

# read JSON into memory
# with open("exampleJSONfromUID.json") as infile:
# with open("exampleJSONfromUIDnoSampleTag.json") as infile:
print(datetime.datetime.now())
filename = 'submission_example.json'
try:
    with open(filename) as infile:
        data = json.load(infile)
except FileNotFoundError:
    print("Could not find the file " + filename)
    exit(1)
except json.decoder.JSONDecodeError as e:
    print("The provided file " + filename + " is not a valid JSON file. Reason: " + str(e))
    exit(1)

data = data['sample']
usi_result = validation.check_usi_structure(data)
validation.deal_with_errors(usi_result)

dup_result = validation.check_duplicates(data)
validation.deal_with_errors(dup_result)

rules = validation.read_in_ruleset("sample_ruleset_v1.3.json")
# pprint.pprint(rules)
print("All sample records have unique data source ids")
ruleset_result = validation.check_with_ruleset(data, rules)
validation.deal_with_validation_results(ruleset_result)

print(datetime.datetime.now())
