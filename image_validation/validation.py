import json
import logging
from typing import Dict, List

from . import misc
from . import Ruleset
from . import ValidationResult
from . import use_ontology
from . import static_parameters

SPECIES = 'Species'
ALLOWED_RELATIONSHIP_NATURE = ['derived from', 'child of', 'same as', 'recurated from']

logger = logging.getLogger(__name__)


# Read in the ruleset from a file
# return a dict which has key as section name and value as another dict (required level as key)
def read_in_ruleset(file: str) -> Ruleset.RuleSet:
    if type(file) is not str:
        raise TypeError("File name must be a string")
    logger.info("read in ruleset")
    result = Ruleset.RuleSet()
    with open(file) as infile:
        data = json.load(infile)
        logger.info("Finished reading the ruleset JSON file")
        for rule_group in data['rule_groups']:
            rule_group_name = rule_group['name']
            logger.debug("Parse rule group " + rule_group_name)
            rule_section = Ruleset.RuleSection(rule_group_name)
            rules = rule_group['rules']
            for rule in rules:
                # field_name = rule['Name']
                if 'Name' not in rule or 'Type' not in rule or 'Required' not in rule or 'Allow Multiple' not in rule:
                    raise KeyError("Each rule must have at least four attributes: Name, Type, "
                                   "Required and Allow Multiple.")
                rule_field = Ruleset.RuleField(rule['Name'], rule['Type'], rule['Required'],
                                               multiple=rule['Allow Multiple'])
                logger.debug("Add Rule " + rule['Name'])
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


# check on the integrity of ruleset
# number and date types must have units
# ontology_id must have allowed terms, but no allowed values
# limited_value must have allowed values, but no allowed terms
# text must not have allowed values
# type      values  units   terms
# number    B       Y       N
# text      N       N       N
# limited   Y       N       N
# ontology  N       N       Y
# uri       B       N       N
# doi       B       N       N
# date      B       Y       N

def check_ruleset(ruleset: Ruleset.RuleSet):
    if type(ruleset) is not Ruleset.RuleSet:
        raise TypeError("The parameter must be of a RuleSet object")
    # conditions
    results: List[str] = []
    for section_name in ruleset.get_all_section_names():
        section_rule = ruleset.get_section_by_name(section_name)
        rules_in_section = section_rule.get_rules()
        for required in rules_in_section.keys():
            for rule_name in rules_in_section[required].keys():
                rule = rules_in_section[required][rule_name]
                rule_type = rule.get_type()
                if rule.get_allowed_values():  # allowed values provided
                    if rule_type == "ontology_id" or rule_type == "text":
                        msg = "Error: No valid values should be provided to field " + rule.get_name() + \
                              " as being of " + rule_type + " type"
                        results.append(msg)
                else:  # no allowed values provided
                    if rule_type == "limited value":
                        msg = "Error: there is no allowed values for field " + rule.get_name() + \
                              " being of " + rule_type + " type"
                        results.append(msg)

                if rule.get_allowed_units():  # units provided
                    if rule_type != "number" and rule_type != "date":
                        msg = "Error: valid units provided for field " + rule.get_name() + " having type as " + \
                              rule_type + " which does not expect units"
                        results.append(msg)
                else:  # no units provided
                    if rule_type == "number" or rule_type == "date":
                        msg = "Error: field " + rule.get_name() + " has type as " + rule_type + \
                              " but no valid units provided"
                        results.append(msg)

                if rule.get_allowed_terms():  # ontology terms provided
                    if rule_type != "ontology_id":
                        msg = "Warning: ontology terms are provided for field " + rule.get_name() + \
                              ". Please re-consider whether it needs to change to ontology_id."
                        results.append(msg)
                else:  # no ontology provided
                    if rule_type == "ontology_id":
                        msg = "Error: No valid terms provided to field " + rule.get_name() + \
                              " which is essential to be of ontology_id type"
                        results.append(msg)

    return results


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
        # check the structure, if wrong, could not continue, so directly skip to next record
        # rather than setting error flag
        if type(one) is not dict:
            result.append(error_prefix + "some records are not represented as hashes")
            continue
        if 'alias' not in one:
            result.append(error_prefix + 'some records do not have alias which is mandatory '
                                         'and used to identify record')
            continue
        else:
            # check existence of mandatory fields
            alias = one['alias']
            if type(alias) is list or type(alias) is dict:
                result.append(error_prefix + "alias can only be a string")
                continue
            count.setdefault(alias, 0)
            count[alias] = count[alias] + 1

        error_flag = False
        if 'title' not in one:
            result.append(error_prefix + "no title field for record with alias as " + alias)
            error_flag = True
        if 'releaseDate' not in one:
            result.append(error_prefix + "no releaseDate field for record with alias as " + alias)
            error_flag = True
        if 'taxonId' not in one:
            result.append(error_prefix + "no taxonId field for record with alias as " + alias)
            error_flag = True
        if 'attributes' not in one:
            result.append(error_prefix + "no attributes for record with alias as " + alias)
            error_flag = True
        # return when previous record has error or current record fails the check above
        if error_flag:
            continue
        # check value of mandatory fields except type of alias
        # which is checked above and duplicate check outside this loop
        # taxonId must be an integer
        if not isinstance(one['taxonId'], int):
            result.append(error_prefix + "taxonId value for record " + alias + " is not an integer")
        # releaseDate needs to be in YYYY-MM-DD
        date_check = misc.get_matched_date(one['releaseDate'], "YYYY-MM-DD")
        if date_check:
            result.append(f"{error_prefix}{date_check} for record with alias value {alias}")
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
        existing_relationships: Dict[str, str] = dict()
        existing_keyword: str = ''
        if 'sampleRelationships' in one:
            relationships = one['sampleRelationships']
            if type(relationships) is not list:
                result.append(
                    error_prefix + "sampleRelationships field must have values within an array for record with "
                    "alias " + alias)
            else:
                for relationship in relationships:
                    if type(relationship) is not dict:
                        result.append(
                            error_prefix + "relationship "
                            "needs to be presented as a hash for record with alias " + alias)
                    else:
                        if len(relationship.keys()) == 2:  # relationship must have two and only two elements
                            if 'alias' in relationship and 'relationshipNature' in relationship:
                                relationship_nature = relationship['relationshipNature']
                                if relationship_nature not in ALLOWED_RELATIONSHIP_NATURE:
                                    result.append(
                                        error_prefix + "Unrecognized relationship nature "
                                        + relationship_nature + " within record " + alias)
                                else:
                                    if relationship_nature != 'same as' and relationship_nature != 'recurated from' \
                                            and existing_keyword != relationship_nature \
                                            and existing_keyword != 'same as'\
                                            and existing_keyword != 'recurated from':
                                        if len(existing_keyword) == 0:
                                            existing_keyword = relationship_nature
                                        else:
                                            result.append(f"{error_prefix}More than one relationship natures found "
                                                          f"within record {alias}")
                                    target = relationship['alias']
                                    if target in existing_relationships:  # already found this in
                                        result.append(f"Duplicated relationship {relationship_nature} with {target} "
                                                      f"for record {alias}")
                                    existing_relationships[target] = relationship['relationshipNature']
                            else:
                                result.append(
                                    error_prefix + "Unrecognized key used (only can be alias and "
                                    "relationshipNature) within one relationship. Affected record " + alias)
                        else:
                            result.append(
                                error_prefix + "two and only two keys (alias and relationshipNature) must be "
                                "presented within every relationship. Affected record " + alias)

    for key in count.keys():
        if count[key] > 1:
            result.append("There are more than one record having " + key + " as its alias")
    return result


# not checking alias duplicates as alias is USI concept and dealt with within check_usi_structure
def check_duplicates(sample: List, id_field: str = 'Data source ID') -> List[str]:
    if type(id_field) is not str:
        raise TypeError("id_field parameter must be a string")
    logger.debug("Check duplicates")
    count = {}
    result = []
    for one in sample:
        # as usi structure has been checked, it is safe to use one['attributes']
        one = one['attributes']
        # idField = locateDataSourceId(one)
        if id_field not in one:
            result.append(
                'At least one record does not have "' + id_field + '" field, maybe wrong case letter '
                'used, please double check')
            return result
        record_id = one[id_field][0]['value']
        if record_id in count:
            count[record_id] = count[record_id] + 1
        else:
            count[record_id] = 1

    for key in count.keys():
        if count[key] > 1:
            result.append("There are more than one record having " + key + " as its "+id_field)
    return result


# example codes consuming the validation result
# expected to be replaced by some codes displaying on the web pages
def deal_with_validation_results(results: List[ValidationResult.ValidationResultRecord], verbose=False) -> Dict:
    count = {'Pass': 0, 'Warning': 0, 'Error': 0}
    vrc_summary: Dict[ValidationResult.ValidationResultColumn, int] = {}
    for result in results:
        overall = result.get_overall_status()
        count[overall] = count[overall] + 1
        if verbose and overall != "Pass":
            logger.info(result.get_messages())

        for vrc in result.get_specific_result_type("error") + result.get_specific_result_type("warning"):
            vrc_summary.setdefault(vrc, 0)
            vrc_summary[vrc] += 1
    return count, vrc_summary


def deal_with_errors(errors: List[str]) -> None:
    for error in errors:
        if type(error) is not str:
            raise TypeError("Error message is not a string")
        logger.info(error)


# check whether value used in place and place accuracy match
def coordinate_check(record: Dict, existing_results: ValidationResult.ValidationResultRecord) -> \
        ValidationResult.ValidationResultRecord:
    if type(record) is not dict:
        raise TypeError("record needs to be a record represented as a Dict")
    if type(existing_results) is not ValidationResult.ValidationResultRecord:
        raise TypeError("The existing results parameter needs to be a ValidationResultRecord object")
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
                ValidationResult.ValidationResultColumn("Error", msg, existing_results.record_id, place_field_name))
    else:
        if record[place_accuracy_field_name][0]['value'] == "missing geographic information":
            msg = "Value " + record[place_field_name][0]['value'] + " provided for field " + place_field_name + \
                  " but value in field " + place_accuracy_field_name + " is missing geographic information"
            existing_results.add_validation_result_column(
                ValidationResult.ValidationResultColumn("Error", msg, existing_results.record_id, place_field_name))
    return existing_results


def species_check(record: Dict, existing_results: ValidationResult.ValidationResultRecord) -> \
        ValidationResult.ValidationResultRecord:
    taxon_id = record['taxonId']
    url = record['attributes'][SPECIES][0]['terms'][0]['url']
    if not url.endswith(str(taxon_id)):
        existing_results.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                "Error", f"taxonId {taxon_id} does not match ontology term used in species {url}",
                existing_results.record_id, ""))
    return existing_results


def check_value_equal(source, target, existing_results, field):
    target_field_value = target['attributes'][field][0]['value']
    source_field_value = source['attributes'][field][0]['value']
    source_label = 'sample'
    target_label = 'related animal'
    if source['attributes']['Material'][0]['value'] == 'organism':
        source_label = 'child'
        target_label = 'parent'

    if target_field_value != source_field_value:
        record_id = existing_results.record_id
        existing_results.add_validation_result_column(ValidationResult.ValidationResultColumn(
            "Error", f"The {field} of {source_label} ({source_field_value}) does not "
            f"match to the {field} of {target_label} ({target_field_value})", record_id, field))
    return existing_results


def animal_sample_check(sample: Dict, animal: Dict, existing_results: ValidationResult.ValidationResultRecord) -> \
        ValidationResult.ValidationResultRecord:
    """
    For now, only check whether sample and animal have the same species
    :param animal:
    :param sample:
    :param existing_results:
    :return:
    """
    if type(animal) is not dict:
        raise TypeError("Animal record needs to be represented as a Dict")
    if type(sample) is not dict:
        raise TypeError("Sample record needs to be represented as a Dict")
    if type(existing_results) is not ValidationResult.ValidationResultRecord:
        raise TypeError("The existing results parameter needs to be a ValidationResultRecord object")

    existing_results = check_value_equal(sample, animal, existing_results, SPECIES)
    return existing_results


def child_of_check(animal: Dict, parents: List, existing_results: ValidationResult.ValidationResultRecord) -> \
        ValidationResult.ValidationResultRecord:
    if type(animal) is not dict:
        raise TypeError("Animal record needs to be represented as a Dict")
    if type(parents) is not list:
        print(type(parents))
        raise TypeError("Parent records need to be represented as a List")
    if type(existing_results) is not ValidationResult.ValidationResultRecord:
        raise TypeError("The existing results parameter needs to be a ValidationResultRecord object")
    for parent in parents:
        existing_results = check_value_equal(animal, parent, existing_results, SPECIES)
        # TODO breed check
    return existing_results


def species_breed_check(animal: Dict, existing_results: ValidationResult.ValidationResultRecord) -> \
        ValidationResult.ValidationResultRecord:
    """
    check whether mapped breed (recommended) matches species
    if mapped breed not found, gives a warning saying no check has been carried out on supplied breed (mandatory)
    :param animal: the animal record to be validated
    :param existing_results: the existing validation result
    :return: the updated validation result
    """
    attrs = animal['attributes']
    # get root breed ontology term based on given species
    species = attrs[SPECIES][0]['value']
    general_breed_from_species: str = use_ontology.get_general_breed_by_species(species)
    general_breed_term = general_breed_from_species['ontologyTerms'].rsplit("/", 1)[1]
    if 'Mapped breed' in attrs:
        mapped_breed = attrs['Mapped breed'][0]['terms'][0]['url']
        match = static_parameters.ontology_library.has_parent(mapped_breed, general_breed_term)
        if not match:
            general_crossbreed_from_species = use_ontology.get_general_breed_by_species(species, cross=True)
            general_crossbreed_term = general_crossbreed_from_species['ontologyTerms'].rsplit("/", 1)[1]
            match = static_parameters.ontology_library.has_parent(mapped_breed, general_crossbreed_term)
            if not match:
                existing_results.add_validation_result_column(
                    ValidationResult.ValidationResultColumn(
                        "Error", f"The mapped breed {mapped_breed} does not match the given species {species}",
                        existing_results.record_id, "Mapped breed"))
    else:
        existing_results.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                "Warning", f"No check has been carried out on whether "
                f"{attrs['Supplied breed'][0]['value']} is a {species} breed as no mapped breed provided",
                existing_results.record_id, "Supplied breed"))
    return existing_results


def parents_sex_check(related, existing_results):
    one_sex: str = related[0]['attributes']['Sex'][0]['value']
    another_sex: str = related[1]['attributes']['Sex'][0]['value']
    unknown_flag = False
    if "unknown sex" in one_sex.lower() or "unknown sex" in another_sex.lower():
        unknown_flag = True
        existing_results.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                "Warning", "At least one parent has unknown value for sex, thus could not be checked",
                existing_results.record_id, "parents sex"))
    if not unknown_flag and one_sex == another_sex:
        existing_results.add_validation_result_column(
            ValidationResult.ValidationResultColumn(
                "Error", "Two parents could not have same sex", existing_results.record_id, "parents sex"))
    return existing_results


def context_validation(record: Dict, existing_results: ValidationResult.ValidationResultRecord, related: List = None) \
        -> ValidationResult.ValidationResultRecord:
    """
    do validation based on context, i.e. value in one field affects allowed values in another field
    or involve more than one record
    :param record: the record data
    :param existing_results: the existing validation result
    :param related: list of the related records either parents or related animal, could be empty list
    :return: updated validation result
    """
    existing_results = coordinate_check(record['attributes'], existing_results)
    existing_results = species_check(record, existing_results)
    record_id = existing_results.record_id
    # existing related records, i.e. having relationships
    if related:
        material = record['attributes']['Material'][0]['value']
        if material == "organism":
            if len(related) > 2:
                existing_results.add_validation_result_column(
                    ValidationResult.ValidationResultColumn(
                        "Error", "Having more than 2 parents defined in sampleRelationships",
                        existing_results.record_id, "sampleRelationships"))
            else:
                existing_results = child_of_check(record, related, existing_results)
                if len(related) == 2:
                    existing_results = parents_sex_check(related, existing_results)
        else:
            if len(related) != 1:
                existing_results.add_validation_result_column(
                    ValidationResult.ValidationResultColumn(
                        "Error", "Specimen can only derive from one animal", record_id, "sampleRelationships"))
            else:
                existing_results = animal_sample_check(record, related[0], existing_results)

    return existing_results
