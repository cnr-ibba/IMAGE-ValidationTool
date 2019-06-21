"""
the ruleset has four levels:
1. the ruleset in the file containing several sections
2. the ruleset section is composed of several rulesets for fields/columns
3. the ruleset for one field which may contains several ontology conditions
    which define which ontology terms are allowed
4. the ontology condition
"""
import logging
import json
from typing import List, Dict

from . import misc
# from . import ValidationResult
from image_validation.ValidationResult import ValidationResultColumn as VRC
from image_validation.ValidationResult import ValidationResultRecord as VRR
from image_validation.ValidationResult import ValidationResultConstant as VRConstants
from . import static_parameters

logger = logging.getLogger(__name__)


class OntologyCondition:
    """
    the class represents conditions to be a valid ontology for the field with ontology_id type
    """
    def __init__(self, term, include_descendant=False, only_leaf=False, include_self=True):
        """
        constructor method
        :param term: ontology short term
        :param include_descendant: indicate whether allow descendants
        :param only_leaf: indicate whether must be a leaf node (i.e. no child)
        :param include_self: indicate whether to include the term itself
        """
        if type(term) is not str:
            raise TypeError("The term parameter must be a string")
        if type(include_self) is not bool:
            raise TypeError("The include_self parameter must be a boolean")
        if type(only_leaf) is not bool:
            raise TypeError("The only_leaf parameter must be a boolean")
        if type(include_descendant) is not bool:
            raise TypeError("The include_descendant parameter must be a boolean")
        self.term = term
        self.include_descendant = include_descendant
        self.only_leaf = only_leaf
        self.include_self = include_self
        ontology = static_parameters.ontology_library.get_ontology(term)
        self.iri = ontology.get_iri()

    def __str__(self):
        """
        Overwrite the method how to construct a string when str(obj) is called
        :return: the representation string of the object
        """
        return f"Term: {self.term} include descendant: {str(self.include_descendant)} " \
            f"leaf only: {str(self.only_leaf)} self included: {str(self.include_self)} iri: {self.iri}"

    def is_leaf_only(self) -> bool:
        """
        :return: whether only leaf node is allowed
        """
        return self.only_leaf

    def is_allowed(self, query: str) -> bool:
        """
        Check whether the query term meets the condition
        :param query: ontology short term
        :return: True if meets the condition
        """
        ontology_detail = static_parameters.ontology_library.get_ontology(query)
        query_iri = ontology_detail.get_iri()
        if self.include_descendant:
            is_child = static_parameters.ontology_library.has_parent(query, self.term)
            if not is_child:
                return False
            # check for extra settings: leaf only, include_self
            if self.only_leaf:  # the term needs to be leaf node
                if not ontology_detail.is_leaf():
                    return False
            # if can not be itself, check whether the same term
            if not self.include_self:  # if could not be itself
                return self.iri != query_iri
            return True
        else:  # not descendant, so only the term itself, no need to consider other settings
            return self.iri == query_iri


class RuleField:
    """
    The class represent a field in the ruleset
    """
    allowed_required = ['mandatory', 'recommended', 'optional']
    allowed_multiple = ['yes', 'max 2', 'no']
    allowed_type = ['number', 'text', 'limited value', 'ontology_id', 'uri', 'doi', 'date']

    def __init__(self, name: str, field_type: str, required: str, multiple: str = 'no', description: str = ""):
        """
        constructor method
        :param name: the field name
        :param field_type: the field type
        :param required: the requirement of the field
        :param multiple: the cardinality of the field
        :param description: the description of the filed, optional
        """
        if type(name) is not str:
            raise TypeError("The name parameter must be a string")
        if type(field_type) is not str:
            raise TypeError("The field_type parameter must be a string")
        if type(required) is not str:
            raise TypeError("The required parameter must be a string")
        if type(multiple) is not str:
            raise TypeError("The multiple parameter must be a string")
        if type(description) is not str:
            raise TypeError("The description parameter must be a string")

        if required not in RuleField.allowed_required:
            allowed_required = ", ".join(RuleField.allowed_required)
            raise ValueError(f"The provided value {required} is not one of {allowed_required}")
        if field_type not in RuleField.allowed_type:
            allowed_types = ", ".join(RuleField.allowed_type)
            raise ValueError(f"The provided value {field_type} is not one of {allowed_types}")
        if multiple not in RuleField.allowed_multiple:
            allowed_multiples = ", ".join(RuleField.allowed_multiple)
            raise ValueError(f"The provided value {multiple} is not one of {allowed_multiples}")

        self.name: str = name
        self.type: str = field_type
        self.required: str = required
        self.multiple: str = multiple
        self.description = description
        self.allowed_values: List[str] = []
        self.allowed_units: List[str] = []
        self.allowed_terms: List[OntologyCondition] = []

    def set_allowed_values(self, values: List[str]) -> None:
        """
        Set the allowed values
        :param values: the list of allowed values
        """
        self.allowed_values: List[str] = []
        for value in values:
            self.allowed_values.append(value)

    def set_allowed_units(self, units: List[str]) -> None:
        """
        Set the allowed units
        :param units: the list of allowed units
        """
        self.allowed_units: List[str] = []
        for unit in units:
            self.allowed_units.append(unit)

    def set_allowed_terms(self, terms: List[Dict[str, str]]) -> None:
        """
        Set the allowed ontology terms
        :param terms: the list of allowed ontology terms
        """
        self.allowed_terms: List[OntologyCondition] = []
        for term in terms:
            descendant = False
            leaf = False
            root = True
            if 'include_root' in term and term['include_root'] == 0:
                root = False
            if 'leaf_only' in term and term['leaf_only'] == 1:
                leaf = True
            if 'allow_descendants' in term and term['allow_descendants'] == 1:
                descendant = True
            condition = OntologyCondition(term['term'], descendant, leaf, root)
            self.allowed_terms.append(condition)

    def get_allowed_values(self) -> List[str]:
        """
        Get the list of allowed values
        :return: the list of allowed values
        """
        return self.allowed_values

    def get_allowed_units(self) -> List[str]:
        """
        Get the list of allowed units
        :return: the list of allowed units
        """
        return self.allowed_units

    def get_allowed_terms(self) -> List[OntologyCondition]:
        """
        Get the list of allowed ontology terms
        :return: the list of allowed ontology terms
        """
        return self.allowed_terms

    def get_required(self) -> str:
        """
        Get the requirement of the field
        :return: the requirement level
        """
        return self.required

    def get_name(self) -> str:
        """
        Get the name of the field
        :return: field name
        """
        return self.name

    def get_type(self) -> str:
        """
        Get the type of the field
        :return: the field type
        """
        return self.type

    def get_multiple(self) -> str:
        """
        Get the cardinality of the field in the string format
        :return: the field cardinality
        """
        return self.multiple

    def allow_multiple(self) -> bool:
        """
        Get whether the field allow multiple values
        :return: True when allowed
        """
        multiple = self.multiple.lower()
        if multiple == 'yes' or multiple == 'max 2':
            return True
        return False

    def check_ontology_allowed(self, short_term: str) -> bool:
        """
        Check whether given ontology term is allowed for the field
        :param short_term: ontology term
        :return: True if allowed
        """
        if type(short_term) is not str:
            raise TypeError("The short_term parameter must be a string")
        for allowed in self.allowed_terms:
            if allowed.is_allowed(short_term):
                return True
        return False

    def validate(self, entries, section_name: str, record_id: str):
        """
        Validate values of one field against the ruleset for that field
        :param entries: field data
        :param section_name: the section the field belong to
        :param record_id: the id of the record
        :return: list of validation result represented as validation column result list
        """
        results: List[VRC] = []
        section_info: str = " (" + section_name + " section)"
        mandatory = False
        if self.required == 'mandatory':
            mandatory = True

        has_error = False
        # check cardinality
        entry_size: int = len(entries)
        if entry_size == 0:
            if mandatory:
                msg = f"Mandatory field {self.name} has empty value"
                results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                has_error = True
            else:
                msg = f"{self.required} field {self.name} has empty value, better remove the field"
                results.append(VRC(VRConstants.WARNING, msg + section_info, record_id, self.name))
        elif entry_size > 1:
            if not self.allow_multiple():
                msg = f"Multiple values supplied for field {self.name} which does not allow multiple values"
                results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                has_error = True
            # multiple only be True (reaching here) when existing Allow Multiple, no need to check existence
            if entry_size > 2 and self.get_multiple() == 'max 2':
                msg = f"Maximum of 2 values allowed for field {self.name} but {str(entry_size)} values provided"
                results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                has_error = True
        # the errors detected above mean that there is no need to validate the actual value(s)
        if has_error:
            return results

        for entry in entries:
            value = entry['value']
            # check units
            allowed_units = self.get_allowed_units()
            allowed_units_str = ', '.join(allowed_units)
            if 'units' in entry:
                if allowed_units:
                    if entry['units'] not in allowed_units:
                        msg = f"{entry['units']} for field {self.name} is not " \
                            f"in the valid units list ({allowed_units_str})"
                        results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                else:  # unit not required, but exists, raise a warning
                    msg = f"No units required but {entry['units']} is used as unit for field {self.name}"
                    results.append(VRC(VRConstants.WARNING, msg + section_info, record_id, self.name))
            else:
                if allowed_units:
                    msg = f"One of {allowed_units_str} need to be present for the field {self.name}"
                    results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
            # check allowed values
            allowed_values = self.get_allowed_values()
            if allowed_values:
                if value not in allowed_values:
                    if self.name == "Availability":
                        # available valid values include example@a.com and no longer available, needs to check for email
                        if not misc.is_url(value):
                            msg = f'<{value}> of field Availability is neither "no longer available" nor a valid URI'
                            results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                    else:  # not availability
                        allowed_values_str = '>, <'.join(allowed_values)
                        msg = f"<{value}> of field {self.name} is not in the valid values list (<{allowed_values_str}>)"
                        results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
            if results:
                return results

            if 'terms' in entry:
                if not self.get_allowed_terms():  # allowed conditions empty
                    msg = f"Ontology provided for field {self.name} however there is no requirement in the ruleset"
                    results.append(VRC(VRConstants.WARNING, msg + section_info, record_id, self.name))
                else:
                    for term in entry['terms']:
                        iri = term['url']
                        if not misc.is_url(iri):
                            msg = f"Invalid URI value {iri} in field {self.name}"
                            results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                            continue

                        term_id = misc.extract_ontology_id_from_iri(iri)
                        if not self.check_ontology_allowed(term_id):
                            msg = f"Not valid ontology term {term_id} in field {self.name}"
                            results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
            if results:
                return results

            # check type
            # current allowed types:
            # numeric: number
            # textual: text, limited value, ontology_id, uri, doi, date
            # number type requires a unit, which is covered in the units check above
            if self.type == 'number':
                if type(value) is not float and type(value) is not int:
                    msg = f"For field {self.name} the provided value {str(value)} is not represented " \
                        f"as/of the expected type Number"
                    results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
            else:  # textual types
                if type(value) is not str:
                    msg = f"For field {self.name} the provided value {str(value)} " \
                        f"is not of the expected type {self.type}"
                    results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                    return results
                # the following tests are based on the value is a string, so need to return above
                if self.type == 'ontology_id':
                    if 'terms' not in entry:
                        msg = f"No url found for the field {self.name} which has the type of ontology_id"
                        results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                    else:
                        for term in entry['terms']:
                            iri = term['url']
                            term = misc.extract_ontology_id_from_iri(iri)
                            ontology = static_parameters.ontology_library.get_ontology(term)
                            if iri != ontology.get_iri():
                                msg = f"Provided iri {iri} does not match the iri " \
                                    f"retrieved from OLS in the field {self.name}"
                                results.append(VRC(VRConstants.WARNING, msg + section_info, record_id, self.name))
                            if not ontology.label_match_ontology(value):
                                if ontology.label_match_ontology(value, False):
                                    msg = f"Provided value {value} has different letter case" \
                                        f" to the term referenced by {iri}"
                                    results.append(VRC(VRConstants.WARNING, msg + section_info, record_id, self.name))
                                else:
                                    msg = f"Provided value {value} does not match to the provided ontology {iri}"
                                    results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                elif self.type == "uri":
                    url_result = misc.is_url(value)
                    if not url_result:
                        msg = f"Invalid URI value {value} for field {self.name}"
                        results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                    else:  # is in URI
                        # in image ruleset, when email provided, it must begin with mailto:
                        if misc.is_email(value):
                            if misc.is_email(value, True):  # the whole value of value is an email, which is wrong
                                msg = f'Email address must have prefix "mailto:" in the field {self.name}'
                                results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                        else:  # it is URL, but not email: could be a normal URL or wrong mailto: location
                            if value.find("mailto:") > 0:
                                msg = f"mailto must be at position 1 to be a valid email value in the field {self.name}"
                                results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                elif self.type == 'doi':
                    doi_result = misc.is_doi(value)
                    if not doi_result:
                        msg = f"Invalid DOI value supplied in the field {self.name}"
                        results.append(VRC(VRConstants.ERROR, msg + section_info, record_id, self.name))
                elif self.type == 'date':
                    # there is always a format(unit) for the date type (checked in the validation.read_in_ruleset)
                    # therefore entry[units] existence should have already been
                    # if 'units' not in entry:
                    date_format = entry['units']
                    date_result = misc.get_matched_date(value, date_format)
                    if date_result:
                        results.append(VRC(VRConstants.ERROR, date_result + section_info, record_id, self.name))

            # it would be safer to skip the validations below as unmatched type detected
            if results:
                return results

        return results


class RuleSection:
    """
    The class represent a section of rulesets which may only apply to a subset of data or to all data records
    depending on the conditions
    """
    def __init__(self, section_name: str):
        """
        Constructor method
        :param section_name: the name of the section
        """
        if type(section_name) is not str:
            raise TypeError("The section_name parameter must be a string")
        self.name = section_name
        # the field ruleset collection organized by the requirement of the field
        self.rules: Dict[str, Dict[str, RuleField]] = {}
        # the conditions when to apply this section of rulesets
        self.conditions: Dict[str, str] = {}
        # rules are organized by requirement first, so this serves as a shortcut
        self.rule_names: Dict[str, int] = {}

    def to_json(self):
        """
        Export as json format
        :return: json representation
        """
        return json.dumps(
                self, default=lambda o: o.__dict__,
                sort_keys=True, indent=2)

    def add_rule(self, rule: RuleField) -> None:
        """
        Add one field rule to the section
        :param rule: the rule for one field
        """
        if type(rule) is not RuleField:
            raise TypeError("The rule parameter must be a RuleField")
        required = rule.get_required()
        name = rule.get_name()
        if required not in self.rules:
            self.rules[required] = {}
        if name in self.rule_names:
            raise ValueError("There are more than one rule related to field " + name)
        self.rules[required][name] = rule
        self.rule_names[name] = 1

    def get_rules(self) -> Dict:
        """
        Get all field rules in the section
        :return: all field rules
        """
        return self.rules

    def get_rule_names(self) -> List[str]:
        """
        Get the list of field names
        :return: the list of field names
        """
        names: List[str] = []
        for name in self.rule_names.keys():
            names.append(name)
        return names

    def get_section_name(self):
        """
        Get the section name
        :return: the name of the section
        """
        return self.name

    def add_condition(self, field, value) -> None:
        """
        Add condition to the section
        :param field: the field on which the condition is checked
        :param value: the value of the field to trigger the condition
        """
        if type(field) is not str:
            raise TypeError("The field parameter must be a string")
        if type(value) is not str:
            raise TypeError("The value parameter must be a string")
        if field in self.conditions:
            raise ValueError("Two conditions apply to the same field")
        self.conditions[field] = value

    def get_conditions(self):
        """
        Get the conditions which determine when the rulesets from the section will be applied
        :return: the conditions
        """
        return self.conditions

    def check_contain_rule_for_field(self, field: str) -> bool:
        """
        Check whether the field existing in the section (based on the assumption every field has the corresponding rule)
        :param field: field name to be checked
        :return: True whether the field exists in the section
        """
        if type(field) is not str:
            raise TypeError("The field parameter must be a string")
        if field in self.rule_names:
            return True
        return False

    def meet_condition(self, record: Dict) -> bool:
        """
        Check whether the record value meets the conditions
        This function is based on that the record meets the USI data format

        :param record: the record data
        :return: True if the record meets the conditions
        """
        if type(record) is not dict:
            raise TypeError("The parameter record must hold a Dict type")
        if 'attributes' not in record:
            raise KeyError("No attributes existing in the record")

        conditions = self.get_conditions()
        attributes = record['attributes']

        for field_name in conditions.keys():
            if field_name not in attributes:
                logger.debug(f"{field_name} used in section conditions could not be found in attributes")
                return False
            else:
                logger.debug("found %s in %s" % (field_name, conditions))

            actual_values = attributes[field_name]
            logger.debug("actual_values is %s" % actual_values)

            found = False

            for value in actual_values:
                if value['value'] == conditions[field_name]:
                    found = True
                    break

            if not found:
                return False
        return True

    def validate(self, attributes: Dict, record_id: str, id_field: str) -> List[VRC]:
        """
        Validate the record using all field rules in the section
        :param attributes: the record attribute values
        :param record_id: the id of the record
        :param id_field: the name of the id field
        :return: list of field validaitn results
        """
        results: List[VRC] = []
        # all mandatory fields must be there, not checking details in this step
        if 'mandatory' in self.rules:
            mandatory_rules = self.rules['mandatory']
            for field_name in mandatory_rules.keys():
                if field_name == id_field:
                    continue
                if field_name not in attributes:
                    msg = f"Mandatory field {field_name} in {self.get_section_name()} section could not be found"
                    results.append(VRC(VRConstants.ERROR, msg, record_id, field_name))
            if results:
                return results
        # check values for all required levels
        for required in self.rules.keys():
            rules = self.rules[required]
            for field_name in rules.keys():
                if field_name in attributes:
                    one_field_result = rules[field_name].validate(attributes[field_name], self.get_section_name(),
                                                                  record_id)
                    for tmp in one_field_result:
                        results.append(tmp)

        return results


class RuleSet:
    """
    The full set of rules
    """
    def __init__(self):
        """
        Constructor method
        """
        self.rule_sections: Dict[str, RuleSection] = {}

    def to_json(self):
        """
        Export as json format
        :return: json representation
        """
        return json.dumps(
                self, default=lambda o: o.__dict__,
                sort_keys=True, indent=2)

    def add_rule_section(self, rule_section: RuleSection) -> None:
        """
        Add a rule section to the set
        :param rule_section: rule section
        :return:
        """
        if type(rule_section) is not RuleSection:
            raise TypeError("The rule section parameter must be a RuleSection object")
        section_name = rule_section.get_section_name()
        if section_name in self.rule_sections:
            raise ValueError("Two rule sections use the same name")
        self.rule_sections[section_name] = rule_section

    def get_all_section_names(self) -> List[str]:
        """
        Get names of all sections
        :return: list of section names
        """
        names: List[str] = []
        for key in self.rule_sections.keys():
            names.append(key)
        return names

    def get_section_by_name(self, section_name: str) -> RuleSection:
        """
        Get rule section by its name
        :param section_name: section name
        :return: the corresponding rule section
        """
        if type(section_name) is not str:
            raise TypeError("The section name must be a string")
        if section_name not in self.rule_sections:
            raise ValueError("No section found according to the given name " + section_name)
        return self.rule_sections.get(section_name)

    def validate(self, record: Dict, id_field: str = 'Data source ID') -> VRR:
        """
        Validate the record with the full ruleset
        :param record: the record data
        :param id_field: the name of the id field, in IMAGE ruleset it is Data source ID
        :return: the validation result
        """
        logger.debug(f"got record: {record}, id_field: {id_field}")
        attributes = record['attributes']
        record_id = attributes[id_field][0]['value']
        record_result = VRR(record_id)

        unmapped = attributes.copy()  # create a copy and remove the ruleset-mapped columns
        del unmapped[id_field]
        for section_name in self.get_all_section_names():
            logger.debug(f"Processing section_name: {section_name}")
            section_rule = self.get_section_by_name(section_name)
            # logger.debug("Got section_rule: %s" % (section_rule.toJSON()))
            if section_rule.meet_condition(record):
                logger.debug("Applying "+section_name+" ruleset to record "+record_id)
                section_results = section_rule.validate(attributes, record_id, id_field)
                for one in section_results:
                    record_result.add_validation_result_column(one)

                for field_name in section_rule.get_rule_names():
                    if field_name in unmapped:
                        del unmapped[field_name]

            else:
                logger.debug(
                    "section_rule %s doesn't meet_condition" % section_name)

        # unmapped column check can only be done here, not in section rule
        # validation as all section rules need to apply
        if unmapped:
            logger.debug("found those unmapped keys: %s" % (unmapped.keys()))

            for key in unmapped.keys():
                record_result.add_validation_result_column(
                    VRC(VRConstants.WARNING, f"Column {key} could not be found in ruleset", record_id, key))
        else:
            logger.debug("No unmapped columns left")

        return record_result
