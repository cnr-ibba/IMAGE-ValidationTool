import json
import logging

from typing import Dict, List

from . import misc
from . import Ruleset
from . import ValidationResult


logger = logging.getLogger(__name__)


# Read in the ruleset from a file
# return a dict which has key as section name and value as another dict (required level as key)
def read_in_ruleset(file: str):
    if type(file) is not str:
        raise TypeError("File name must be a string")
    logger.info("read in ruleset")
    result = Ruleset.RuleSet()
    with open(file) as infile:
        data = json.load(infile)
        logger.info("Finished reading the ruleset JSON file")
        for rule_group in data['rule_groups']:
            rule_group_name = rule_group['name']
            logger.debug("Parse rule group "+rule_group_name)
            rule_section = Ruleset.RuleSection(rule_group_name)
            rules = rule_group['rules']
            for rule in rules:
                # field_name = rule['Name']
                rule_field = Ruleset.RuleField(rule['Name'], rule['Type'], rule['Required'],
                                               multiple=rule['Allow Multiple'])
                logger.debug("Add Rule "+rule['Name'])
                if "Valid values" in rule:
                    rule_field.set_allowed_values(rule["Valid values"])
                if "Valid units" in rule:
                    rule_field.set_allowed_units(rule["Valid units"])
                if "Valid terms" in rule:
                    rule_field.set_allowed_terms(rule["Valid terms"])
                rule_section.add_rule(rule_field)
            if 'condition' in rule_group and 'attribute_value_match' in rule_group['condition']:
                conditions = rule_group['condition']['attribute_value_match']
                for field in conditions.keys():
                    rule_section.add_condition(field, conditions[field])
            result.add_rule_section(rule_section)
    return result


# the samples are stored in the JSON format which is compatible with USI
# details see https://drive.google.com/open?id=1OwSuusnPzIvF2wzSfPp6ElGgH_jr7qyDgBXb41zB3QY
# this function checks for USI JSON format only, nothing to do with the IMAGE ruleset
# therefore not using ValidationResultRecord class
def check_usi_structure(sample: List[Dict]):
    logger.debug("Check whether data meets USI data format standard")
    count: Dict[str, int] = {}
    result: List[str] = []
    error_prefix = 'Wrong JSON structure: '
    if type(sample) is not list:
        result.append(error_prefix + "all data need to be encapsulated in an array")
        return result
    for one in sample:
        # check existence of mandatory fields
        if type(one) is not dict:
            result.append(error_prefix + "some records are not represented as hashes")
            return result
        if 'alias' not in one:
            result.append(error_prefix + 'some records do not have alias which is mandatory '
                                         'and used to identify record')
            return result
        else:
            alias = one['alias']
            if type(alias) is list or type(alias) is dict:
                result.append(error_prefix + "alias can only be a string")
                return result
            if alias in count:
                count[alias] = count[alias] + 1
            else:
                count[alias] = 1
        if 'title' not in one:
            result.append(error_prefix + "no title field for record with alias as " + alias)
        if 'releaseDate' not in one:
            result.append(error_prefix + "no releaseDate field for record with alias as " + alias)
        if 'taxonId' not in one:
            result.append(error_prefix + "no taxonId field for record with alias as " + alias)
        if 'attributes' not in one:
            result.append(error_prefix + "no attributes for record with alias as " + alias)
        # check value of mandatory fields except type of alias
        # which is checked above and duplicate check outside this loop
        # taxonId must be an integer
        if not isinstance(one['taxonId'], int):
            result.append(error_prefix + "taxonId value for record " + alias + " is not an integer")
        # releaseDate needs to be in YYYY-MM-DD
        date_check = misc.get_matched_date(one['releaseDate'], "YYYY-MM-DD")
        if date_check:
            result.append(error_prefix + date_check + " for record with alias value " + alias)
        # attributes is a list of attributes, represented as dict
        attrs = one['attributes']
        if type(attrs) is not dict:
            result.append(error_prefix + "attributes must be stored as a map for record with alias " + alias)
        else:
            for attr_name in attrs:
                attr_values = attrs[attr_name]
                if type(attr_values) is not list:
                    result.append(
                        error_prefix +
                        "the values for attribute " + attr_name + " needs to be in an array for record " + alias)
                else:
                    for attr_value in attr_values:
                        if type(attr_value) is not dict:
                            result.append(
                                error_prefix + "the attribute value of " + attr_name +
                                " needs to be represented as a map in record " + alias)
                        else:
                            if 'value' not in attr_value:
                                result.append(
                                    error_prefix + "could not find 'value' keyword for attribute "
                                    + attr_name + " in record " + alias)
                            else:
                                for key in attr_value.keys():
                                    if key != 'value' and key != 'units' and key != 'terms':
                                        result.append(
                                            error_prefix + "Unrecognized keyword " + key + " used in attribute "
                                            + attr_name + " in record " + alias)
                                    elif key == 'terms':
                                        terms_value = attr_value[key]
                                        if type(terms_value) is not list:
                                            msg = error_prefix + 'ontology terms need to be stored ' \
                                                                 'in an array in record ' + alias
                                            result.append(msg)
                                        elif type(terms_value[0]) is not dict or ('url' not in terms_value[0]):
                                            result.append(
                                                error_prefix +
                                                "url not used as key for ontology term in record " + alias)

        # optional field
        if 'sampleRelationships' in one:
            relationships = one['sampleRelationships']
            if type(relationships) is not list:
                result.append(
                    "Wrong JSON structure: sampleRelationships field must have values within an array for record with "
                    "alias " + alias)
            else:
                for relationship in relationships:
                    if type(relationship) is not dict:
                        result.append(
                            "Wrong JSON structure: relationship "
                            "needs to be presented as a hash for record with alias " + alias)
                    else:
                        if len(relationship.keys()) == 2:
                            if 'alias' in relationship and 'relationshipNature' in relationship:
                                relationship_nature = relationship['relationshipNature']
                                if relationship_nature != 'derived from' and \
                                        relationship_nature != 'child of' and \
                                        relationship_nature != 'same as' and \
                                        relationship_nature != 'recurated from':
                                    result.append(
                                        "Wrong JSON structure: Unrecognized relationship nature "
                                        + relationship_nature + " within record " + alias)
                            else:
                                result.append(
                                    "Wrong JSON structure: Unrecognized key used (only can be alias and "
                                    "relationshipNature) within one relationship. Affected record " + alias)
                        else:
                            result.append(
                                "Wrong JSON structure: two and only two keys (alias and relationshipNature) must be "
                                "presented within every relationship. Affected record " + alias)

    for key in count.keys():
        if count[key] > 1:
            result.append("There are more than one record having " + key + " as its alias")
    return result


# not checking alias duplicates as alias is USI concept and dealt with within check_usi_structure
def check_duplicates(sample: List) -> List[str]:
    logger.debug("Check duplicates")
    count = {}
    result = []
    for one in sample:
        # as usi structure has been checked, it is safe to use one['attributes']
        one = one['attributes']
        # idField = locateDataSourceId(one)
        id_field = 'Data source ID'
        if id_field not in one:
            result.append(
                'At least one record does not have "Data source ID", maybe wrong case letter '
                'used for "Data source ID", please double check')
            return result
        record_id = one[id_field][0]['value']
        if record_id in count:
            count[record_id] = count[record_id] + 1
        else:
            count[record_id] = 1

    for key in count.keys():
        if count[key] > 1:
            result.append("There are more than one record having " + key + " as its data source id")
    return result


# example codes consuming the validation result
# expected to be replaced by some codes displaying on the web pages
def deal_with_validation_results(results: List[ValidationResult.ValidationResultRecord]) -> None:
    count = {'Pass': 0, 'Warning': 0, 'Error': 0}
    for result in results:
        overall = result.get_overall_status()
        count[overall] = count[overall] + 1
        if overall != "Pass":
            print(result.get_messages())
    print(count)


def deal_with_errors(errors) -> None:
    for error in errors:
        print(error)


# check whether value used in place and place accuracy match
def coordinate_check(record: Dict, existing_results: ValidationResult.ValidationResultRecord)->\
        ValidationResult.ValidationResultRecord:
    material = record['Material'][0]['value']
    if material == "organism":
        place_field_name = "Birth location"
    else:
        place_field_name = "Collection place"
    place_accuracy_field_name = place_field_name + " accuracy"
    if place_field_name not in record:
        if record[place_accuracy_field_name][0]['value'] != "missing geographic information":
            msg = "No value provided for field " + place_field_name + " but value in field " + \
                  place_accuracy_field_name + " is not missing geographic information"
            existing_results.add_validation_result_column(
                ValidationResult.ValidationResultColumn("Error", msg, existing_results.record_id))
    else:
        if record[place_accuracy_field_name][0]['value'] == "missing geographic information":
            msg = "Value " + record[place_field_name][0]['value'] + " provided for field " + place_field_name + \
                  " but value in field " + place_accuracy_field_name + " is missing geographic information"
            existing_results.add_validation_result_column(
                ValidationResult.ValidationResultColumn("Error", msg, existing_results.record_id))
    return existing_results


# do validation based on context, i.e. value in one field affects allowed values in another field
def context_validation(record: Dict, existing_results: ValidationResult.ValidationResultRecord)->\
        ValidationResult.ValidationResultRecord:
    existing_results = coordinate_check(record, existing_results)
    # other context based validations
    return existing_results
