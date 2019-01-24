import json
import logging

from . import misc

from . import use_ontology
from . import ValidationResult
from typing import Dict, List

logger = logging.getLogger(__name__)
ontology_libraries = use_ontology.OntologyCache()


# Read in the ruleset from a file
# return a dict which has key as section name and value as another dict (required level as key)
def read_in_ruleset(file: str) -> Dict[str, Dict]:
    logger.debug("read in ruleset")
    result = {}
    with open(file) as infile:
        data = json.load(infile)
        for rule_group in data['rule_groups']:
            rule_group_name = rule_group['name']
            rules = rule_group['rules']
            for rule in rules:
                # field_name = rule['Name']
                required = rule['Required']
                if rule_group_name not in result:
                    result[rule_group_name] = {}
                if required not in result[rule_group_name]:
                    result[rule_group_name][required] = []
                result[rule_group_name][required].append(rule)

    return result


# obsolete after agreeing field name should be the exact match
def find_used_field_name(record: Dict, camel_case_str: str) -> str:
    field_name = camel_case_str
    if field_name not in record:
        field_name = misc.from_lower_camel_case(camel_case_str)
        if field_name not in record:
            field_name = ""
    return field_name


# obsolete after agreeing field name should be the exact match
def locate_data_source_id(record: Dict) -> str:
    id_field = find_used_field_name(record, 'dataSourceId')
    if len(id_field) == 0:
        id_field = 'Data source ID'
        if id_field not in record:
            id_field = ""
    return id_field


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


# entries is the value of the attribute in the form of array
# rule is a dict, the rule for the field
# section is a string, indicating which section (standard, animal, sample) the field belongs to
# record_id: the id of the record
# return list of ValidationResultColumn object for one field
def validate_one_field(entries: List, rule: Dict, section: str, record_id: str):
    column_results: List[ValidationResult.ValidationResultColumn] = []
    section_info: str = " ("+section+" section)"
    # set rule attribute
    multiple: bool = False
    if 'Allow Multiple' in rule and (rule['Allow Multiple'] == 'yes' or rule['Allow Multiple'] == 'max 2'):
        multiple = True

    mandatory = False
    if 'Required' in rule and rule['Required'] == 'mandatory':
        mandatory = True

    # read in allowed ontologies
    allowed_conditions: List[OntologyCondition] = []
    if 'Valid terms' in rule:
        for term in rule['Valid terms']:
            if 'term' in term:
                descendant = False
                leaf = False
                root = True
                if 'include_root' in term and term['include_root'] == 0:
                    root = False
                if 'leaf_only' in term and term['leaf_only'] == 1:
                    leaf = True
                if 'allow_descendants' in term and term['allow_descendants'] == 1:
                    descendant = True
                ontology_condition = OntologyCondition(term['term'], descendant, leaf, root)
                allowed_conditions.append(ontology_condition)

    # check cardinality
    entry_size: int = len(entries)
    if entry_size == 0:
        if mandatory:
            msg = "Mandatory field " + rule['Name'] + " has empty value"
            column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
        else:
            msg = rule['Required'] + " field " + rule['Name'] + " has empty value, better remove the field"
            column_results.append(ValidationResult.ValidationResultColumn("Warning", msg+section_info, record_id))
    elif entry_size > 1:
        if not multiple:
            msg = "Multiple values supplied for field " + rule['Name'] + " which does not allow multiple values"
            column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
        # multiple only be True (reaching here) when existing Allow Multiple, no need to check existence
        if entry_size > 2 and rule['Allow Multiple'] == 'max 2':
            msg = "Maximum of 2 values allowed for field " \
                  + rule['Name'] + " but " + str(entry_size) + " values provided"
            column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
    # the errors detected above mean that there is no need to validate the actual value(s)
    if column_results:
        return column_results

    for entry in entries:
        value = entry['value']
        # check units
        if 'units' in entry:
            if 'Valid units' in rule:
                if entry['units'] not in rule['Valid units']:
                    msg = entry['units'] + " for field " + rule['Name'] \
                          + " is not in the valid units list (" + ', '.join(rule['Valid units']) + ")"
                    column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
            else:  # unit not required, but exists, raise a warning
                msg = "No units required but " + entry['units'] + " is used as unit"
                column_results.append(ValidationResult.ValidationResultColumn("Warning", msg+section_info, record_id))
        else:
            if 'Valid units' in rule:
                msg = "One of " + ', '.join(rule['Valid units']) + " need to be present for the field " + rule['Name']
                column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
        # check allowed values
        if 'Valid values' in rule:
            if value not in rule['Valid values']:
                if rule['Name'] == "Availability":
                    # available valid values include example@a.com and no longer available, needs to check for email
                    if not misc.is_email(value):
                        msg = '<' + value + '> of field Availability is ' \
                                            'neither "no longer available" nor a valid mailto URI'
                        column_results.append(ValidationResult.ValidationResultColumn("Error",
                                                                                      msg+section_info, record_id))
                else:
                    msg = "<" + value + "> of field " + rule[
                        'Name'] + " is not in the valid values list (<" + '>, <'.join(rule['Valid values']) + ">)"
                    column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
        if column_results:
            return column_results

        if 'terms' in entry:
            if not allowed_conditions:  # allowed conditions empty
                msg = "Ontology provided for field "+rule['Name']+" however there is no requirement in the ruleset"
                column_results.append(ValidationResult.ValidationResultColumn("Warning", msg+section_info, record_id))
            else:
                for term in entry['terms']:
                    valid = False
                    iri = term['url']
                    if not misc.is_uri(iri):
                        msg = "Invalid URI value " + iri + " in field " + rule['Name']
                        column_results.append(ValidationResult.ValidationResultColumn("Error",
                                                                                      msg+section_info, record_id))
                        continue
                    term_id = misc.extract_ontology_id_from_iri(iri)

                    for allowed in allowed_conditions:
                        if allowed.is_allowed(term_id):
                            valid = True
                            break
                    if not valid:
                        msg = 'Not valid ontology term '+term_id+' in field ' + rule['Name']
                        column_results.append(ValidationResult.ValidationResultColumn("Error",
                                                                                      msg+section_info, record_id))

        # check type
        # current allowed types:
        # numeric: number
        # textual: text, limited value, ontology_id, uri, doi, date
        # number type requires a unit, which is covered in the units check above
        if rule['Type'] == 'number':
            if type(value) is not float and type(value) is not int:
                msg = "For field " + rule['Name'] + " the provided value " + str(
                    value) + " is not of the expected type Number"
                column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
        else:  # textual types
            if type(value) is not str:
                msg = "For field " + rule['Name'] + " the provided value " + str(
                    value) + " is not of the expected type " + rule['Type']
                column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
            if rule['Type'] == 'ontology_id':
                if 'terms' not in entry:
                    msg = "No url found for the field "+rule['Name']+" which has the type of ontology_id "
                    column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
                else:
                    for term in entry['terms']:
                        iri = term['url']
                        term = misc.extract_ontology_id_from_iri(iri)
                        ontology = ontology_libraries.get_ontology(term)
                        if iri != ontology.get_iri():
                            msg = "Provided iri "+iri+" does not match the iri retrieved from OLS in the field "\
                                  + rule['Name']
                            column_results.append(
                                ValidationResult.ValidationResultColumn("Warning", msg + section_info, record_id))
                        if not ontology.label_match_ontology(value):
                            if ontology.label_match_ontology(value, False):
                                msg = "Provided value " + value + \
                                      " has different letter case to the term referenced by " + iri
                                column_results.append(
                                    ValidationResult.ValidationResultColumn("Warning", msg+section_info, record_id))
                            else:
                                msg = "Provided value "+value+" does not match to the provided ontology "+iri
                                column_results.append(
                                    ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
            elif rule['Type'] == "uri":
                uri_result = misc.is_uri(value)
                if not uri_result:
                    msg = "Invalid URI value " + value + " for field " + rule['Name']
                    column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
                else:  # is in URI
                    # in image ruleset, when email provided, it must begin with mailto:
                    if misc.is_email(value):
                        if misc.is_email(value, True):  # the whole value of value is an email, which is wrong
                            msg = 'Email address must have prefix "mailto:" in the field ' + rule['Name']
                            column_results.append(
                                ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
                        else:
                            if value.find("mailto:") != 0:
                                msg = "Unrecognized mailto value in the field " + rule['Name']
                                column_results.append(
                                    ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
            elif rule['Type'] == 'doi':
                doi_result = misc.is_doi(value)
                if doi_result:
                    msg = "Invalid DOI value supplied in the field " + rule['Name']
                    column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
            elif rule['Type'] == 'date':
                # there is always a format(unit) for the date type
                if 'units' not in entry:
                    msg = "No date format found as unit in the field " + rule['Name']
                    column_results.append(ValidationResult.ValidationResultColumn("Error", msg+section_info, record_id))
                else:
                    date_format = entry['units']
                    date_result = misc.get_matched_date(value, date_format)
                    if date_result:
                        column_results.append(
                            ValidationResult.ValidationResultColumn("Error", date_result+section_info, record_id))

        # it would be safer to skip the validations below as unmatched type detected
        if column_results:
            return column_results
    return column_results


# check whether all mandatory fields are present
# check all fields in the data could be found within ruleset
def check_with_ruleset(sample: List[Dict], ruleset: Dict[str, Dict]) -> List[ValidationResult.ValidationResultRecord]:
    submission_result = []
    for one in sample:
        one = one['attributes']
        id_field = 'Data source ID'
        record_id = one[id_field][0]['value']
        record_result = ValidationResult.ValidationResultRecord(record_id)
        logger.debug("Validate record "+record_id)

        material_field = 'Material'
        if material_field not in one:
            error = ValidationResult.ValidationResultColumn(
                "Error", 'does not have mandatory field "Material"', record_id)
            record_result.add_validation_result_column(error)
            submission_result.append(record_result)
            continue

        unmapped = one.copy()  # create a copy and remove the ruleset-mapped columns
        del unmapped[id_field]
        for section in ruleset.keys():
            # apply both standard and material type specific sections
            if section != 'standard' and section != one[material_field][0]['value']:
                continue
            section_rules = ruleset[section]
            # only check whether mandatory fields exist or not, not check the actual value which could be empty
            if 'mandatory' in section_rules:
                mandatory_rules = section_rules['mandatory']
                for mandatory_rule in mandatory_rules:
                    field_name = mandatory_rule['Name']
                    if field_name == id_field:
                        continue
                    if field_name not in one:
                        msg = "Mandatory field " + field_name + " in " + section + " section could not be found"
                        record_result.add_validation_result_column(
                            ValidationResult.ValidationResultColumn("Error", msg, record_id))
            # check values for all required levels
            for required in section_rules.keys():
                rules = section_rules[required]
                for rule in rules:
                    field_name = rule['Name']
                    if field_name in unmapped:

                        one_field_result = validate_one_field(one[field_name], rule, section, record_id)
                        if one_field_result:
                            for tmp in one_field_result:
                                record_result.add_validation_result_column(tmp)
                        del unmapped[field_name]
        if unmapped:
            for key in unmapped.keys():
                record_result.add_validation_result_column(
                    ValidationResult.ValidationResultColumn(
                        "Warning", "Column " + key + " could not be found in ruleset", record_id))
        if record_result.is_empty():
            record_result.add_validation_result_column(
                ValidationResult.ValidationResultColumn("Pass", "", record_id))
        submission_result.append(record_result)
    return submission_result


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


class OntologyCondition:

    def __init__(self, term, include_descendant=False, only_leaf=False, include_self=True, iri=None):
        self.term = term
        self.include_descendant = include_descendant
        self.only_leaf = only_leaf
        self.include_self = include_self
        try:
            if iri:
                self.iri = iri
            else:
                ontology = ontology_libraries.get_ontology(term)
                self.iri = ontology.get_iri()
        except TypeError:
            print(term)
            exit()

    def __str__(self):
        return "Term: " + self.term + " include descendant: " + str(self.include_descendant) + " leaf only: " + \
               str(self.only_leaf) + " self included: " + str(self.include_self) + " iri: " + self.iri

    def is_leaf_only(self) -> bool:
        return self.only_leaf

    def is_allowed(self, query: str) -> bool:
        ontology_detail = ontology_libraries.get_ontology(query)
        query_iri = ontology_detail.get_iri()
        if self.include_descendant:
            is_child = ontology_libraries.has_parent(query, self.term)
            if not is_child:
                return False
            # check for extra settings: leaf only, include_self
            if self.only_leaf:  # the term needs to be leaf node
                if not ontology_detail.is_leaf():
                    return False
            if not self.include_self:  # if could not be itself
                return self.iri != query_iri
            return True
        else:  # not descendant, so only the term itself, no need to consider other settings
            return self.iri == query_iri
