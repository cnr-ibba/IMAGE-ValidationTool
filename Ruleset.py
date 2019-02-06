import logging
import misc
import validation
import ValidationResult
import use_ontology
from typing import List, Dict

logger = logging.getLogger(__name__)

ontology_libraries = use_ontology.OntologyCache()


class OntologyCondition:

    def __init__(self, term, include_descendant=False, only_leaf=False, include_self=True, iri=None):
        if type(term) is not str:
            raise TypeError("The term parameter must be a string")
        if type(include_self) is not bool:
            raise TypeError("The include_self parameter must be a boolean")
        if type(only_leaf) is not bool:
            raise TypeError("The only_leaf parameter must be a boolean")
        if type(include_descendant) is not bool:
            raise TypeError("The include_descendant parameter must be a boolean")
        if iri is not None and type(iri) is not str:
            raise TypeError("The iri parameter must be a string")
        self.term = term
        self.include_descendant = include_descendant
        self.only_leaf = only_leaf
        self.include_self = include_self
        try:
            if iri:
                self.iri = iri
            else:
                ontology = validation.ontology_libraries.get_ontology(term)
                self.iri = ontology.get_iri()
        except TypeError:
            print(term)

    def __str__(self):
        return "Term: " + self.term + " include descendant: " + str(self.include_descendant) + " leaf only: " + \
               str(self.only_leaf) + " self included: " + str(self.include_self) + " iri: " + self.iri

    def is_leaf_only(self) -> bool:
        return self.only_leaf

    def is_allowed(self, query: str) -> bool:
        ontology_detail = validation.ontology_libraries.get_ontology(query)
        query_iri = ontology_detail.get_iri()
        if self.include_descendant:
            is_child = validation.ontology_libraries.has_parent(query, self.term)
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


class RuleField:
    allowed_required = ['mandatory', 'recommended', 'optional']
    allowed_multiple = ['yes', 'max 2', 'no']
    allowed_type = ['number', 'text', 'limited value', 'ontology_id', 'uri', 'doi', 'date']

    def __init__(self, name: str, field_type: str, required: str, multiple: str = 'no', description: str = ""):
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
            raise ValueError(
                "The provided value " + required + " is not one of " + ", ".join(RuleField.allowed_required))
        if field_type not in RuleField.allowed_type:
            raise ValueError("The provided value " + field_type + " is not one of " + ", ".join(RuleField.allowed_type))
        if multiple not in RuleField.allowed_multiple:
            raise ValueError(
                "The provided value " + multiple + " is not one of " + ", ".join(RuleField.allowed_multiple))

        self.name: str = name
        self.type: str = field_type
        self.required: str = required
        self.multiple: str = multiple
        self.description = description
        self.allowed_values: List[str] = []
        self.allowed_units: List[str] = []
        self.allowed_terms: List[OntologyCondition] = []

    def set_allowed_values(self, values: List[str]):
        for value in values:
            self.allowed_values.append(value)

    def set_allowed_units(self, units: List[str]):
        for unit in units:
            self.allowed_units.append(unit)

    def set_allowed_terms(self, terms: List[Dict[str, str]]):
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
        return self.allowed_values

    def get_allowed_units(self) -> List[str]:
        return self.allowed_units

    def get_allowed_terms(self) -> List[OntologyCondition]:
        return self.allowed_terms

    def get_required(self) -> str:
        return self.required

    def get_name(self) -> str:
        return self.name

    def get_multiple(self) -> str:
        return self.multiple

    def allow_multiple(self) -> bool:
        multiple = self.multiple.lower()
        if multiple == 'yes' or multiple == 'max 2':
            return True
        return False

    def check_ontology_allowed(self, short_term: str) -> bool:
        if type(short_term) is not str:
            raise TypeError("The short_term parameter must be a string")
        for allowed in self.allowed_terms:
            if allowed.is_allowed(short_term):
                return True
        return False

    def validate(self, entries, section_name: str, record_id: str):
        results: List[ValidationResult.ValidationResultColumn] = []
        section_info: str = " (" + section_name + " section)"
        mandatory = False
        if self.required == 'mandatory':
            mandatory = True

        # check cardinality
        entry_size: int = len(entries)
        if entry_size == 0:
            if mandatory:
                msg = "Mandatory field " + self.name + " has empty value"
                results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
            else:
                msg = self.required + " field " + self.name + " has empty value, better remove the field"
                results.append(ValidationResult.ValidationResultColumn("Warning", msg + section_info, record_id))
        elif entry_size > 1:
            if not self.allow_multiple():
                msg = "Multiple values supplied for field " + self.name + " which does not allow multiple values"
                results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
            # multiple only be True (reaching here) when existing Allow Multiple, no need to check existence
            if entry_size > 2 and self.get_multiple() == 'max 2':
                msg = "Maximum of 2 values allowed for field " \
                      + self.name + " but " + str(entry_size) + " values provided"
                results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
        # the errors detected above mean that there is no need to validate the actual value(s)
        if results:
            return results

        for entry in entries:
            value = entry['value']
            # check units
            allowed_units = self.get_allowed_units()
            if 'units' in entry:
                if allowed_units:
                    if entry['units'] not in allowed_units:
                        msg = entry['units'] + " for field " + self.name \
                              + " is not in the valid units list (" + ', '.join(allowed_units) + ")"
                        results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                else:  # unit not required, but exists, raise a warning
                    msg = "No units required but " + entry['units'] + " is used as unit"
                    results.append(ValidationResult.ValidationResultColumn("Warning", msg + section_info, record_id))
            else:
                if allowed_units:
                    msg = "One of " + ', '.join(allowed_units) + " need to be present for the field " + self.name
                    results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
            # check allowed values
            allowed_values = self.get_allowed_values()
            if allowed_values:
                if value not in allowed_values:
                    if self.name == "Availability":
                        # available valid values include example@a.com and no longer available, needs to check for email
                        if not misc.is_email(value):
                            msg = '<' + value + '> of field Availability is ' \
                                                'neither "no longer available" nor a valid mailto URI'
                            results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info,
                                                                                   record_id))
                    else:  # not availability
                        msg = "<" + value + "> of field " + self.name + \
                              " is not in the valid values list (<" + '>, <'.join(allowed_values) + ">)"
                        results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
            if results:
                return results

            if 'terms' in entry:
                if not self.get_allowed_terms():  # allowed conditions empty
                    msg = "Ontology provided for field " + self.name + " however there is no requirement in the ruleset"
                    results.append(ValidationResult.ValidationResultColumn("Warning", msg + section_info, record_id))
                else:
                    for term in entry['terms']:
                        iri = term['url']
                        if not misc.is_uri(iri):
                            msg = "Invalid URI value " + iri + " in field " + self.name
                            results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info,
                                                                                   record_id))
                            continue

                        term_id = misc.extract_ontology_id_from_iri(iri)
                        if not self.check_ontology_allowed(term_id):
                            msg = 'Not valid ontology term ' + term_id + ' in field ' + self.name
                            results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info,
                                                                                   record_id))

            # check type
            # current allowed types:
            # numeric: number
            # textual: text, limited value, ontology_id, uri, doi, date
            # number type requires a unit, which is covered in the units check above
            if self.type == 'number':
                if type(value) is not float and type(value) is not int:
                    msg = "For field " + self.name + " the provided value " + str(value)\
                          + " is not of the expected type Number"
                    results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
            else:  # textual types
                if type(value) is not str:
                    msg = "For field " + self.name + " the provided value " + str(value)\
                          + " is not of the expected type " + self.type
                    results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                if self.type == 'ontology_id':
                    if 'terms' not in entry:
                        msg = "No url found for the field " + self.name + " which has the type of ontology_id "
                        results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                    else:
                        for term in entry['terms']:
                            iri = term['url']
                            term = misc.extract_ontology_id_from_iri(iri)
                            ontology = ontology_libraries.get_ontology(term)
                            if iri != ontology.get_iri():
                                msg = "Provided iri " + iri + \
                                      " does not match the iri retrieved from OLS in the field " + self.name
                                results.append(
                                    ValidationResult.ValidationResultColumn("Warning", msg + section_info, record_id))
                            if not ontology.label_match_ontology(value):
                                if ontology.label_match_ontology(value, False):
                                    msg = "Provided value " + value + \
                                          " has different letter case to the term referenced by " + iri
                                    results.append(ValidationResult.ValidationResultColumn("Warning",
                                                                                        msg + section_info, record_id))
                                else:
                                    msg = "Provided value " + value + " does not match to the provided ontology " + iri
                                    results.append(
                                        ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                elif self.type == "uri":
                    uri_result = misc.is_uri(value)
                    if not uri_result:
                        msg = "Invalid URI value " + value + " for field " + self.name
                        results.append(
                            ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                    else:  # is in URI
                        # in image ruleset, when email provided, it must begin with mailto:
                        if misc.is_email(value):
                            if misc.is_email(value, True):  # the whole value of value is an email, which is wrong
                                msg = 'Email address must have prefix "mailto:" in the field ' + rule['Name']
                                results.append(
                                    ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                            else:
                                if value.find("mailto:") != 0:
                                    msg = "Unrecognized mailto value in the field " + self.name
                                    results.append(
                                        ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                elif self.type == 'doi':
                    doi_result = misc.is_doi(value)
                    if doi_result:
                        msg = "Invalid DOI value supplied in the field " + self.name
                        results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                elif self.type == 'date':
                    # there is always a format(unit) for the date type
                    if 'units' not in entry:
                        msg = "No date format found as unit in the field " + self.name
                        results.append(ValidationResult.ValidationResultColumn("Error", msg + section_info, record_id))
                    else:
                        date_format = entry['units']
                        date_result = misc.get_matched_date(value, date_format)
                        if date_result:
                            results.append(
                                ValidationResult.ValidationResultColumn("Error", date_result + section_info, record_id))

            # it would be safer to skip the validations below as unmatched type detected
            if results:
                return results

        return results


class RuleSection:

    def __init__(self, section_name: str):
        if type(section_name) is not str:
            raise TypeError("The section_name parameter must be a string")
        self.name = section_name
        self.rules: Dict[str, Dict[str, RuleField]] = {}
        self.conditions: Dict[str, str] = {}
        # rules are organized by requirement first, so this serves as a shortcut
        self.rule_names: Dict[str, int] = {}

    def add_rule(self, rule: RuleField):
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

    def get_rules(self):
        return self.rules

    def get_rule_names(self):
        names: List[str] = []
        for name in self.rule_names.keys():
            names.append(name)
        return names

    def get_section_name(self):
        return self.name

    def add_condition(self, field, value):
        if type(field) is not str:
            raise TypeError("The field parameter must be a string")
        if type(value) is not str:
            raise TypeError("The value parameter must be a string")
        if field in self.conditions:
            raise ValueError("Two conditions apply to the same field")
        self.conditions[field] = value

    def get_conditions(self):
        return self.conditions

    def check_contain_rule_for_field(self, field: str) -> bool:
        if type(field) is not str:
            raise TypeError("The field parameter must be a string")
        if field in self.rule_names:
            return True
        return False

    # based on the assumption that record meet the USI data format
    def meet_condition(self, record: Dict) -> bool:
        if type(record) is not dict:
            raise TypeError("The parameter record must hold a Dict type")
        if 'attributes' not in record:
            raise KeyError("No attributes existing in the record")
        conditions = self.get_conditions()
        attributes = record['attributes']
        for field_name in conditions.keys():
            if field_name not in attributes:
                return False
            actual_values = attributes[field_name]
            found = False
            for value in actual_values:
                if value['value'] == conditions[field_name]:
                    found = True
                    break
            if not found:
                return False
        return True

    def validate(self, attributes: Dict, record_id: str, id_field: str) -> List[ValidationResult.ValidationResultColumn]:
        results: List[ValidationResult.ValidationResultColumn] = []
        # all mandatory fields must be there, not checking details in this step
        if 'mandatory' in self.rules:
            mandatory_rules = self.rules['mandatory']
            for field_name in mandatory_rules.keys():
                if field_name == id_field:
                    continue
                if field_name not in attributes:
                    msg = "Mandatory field " + field_name + " in " + self.get_section_name() \
                          + " section could not be found"
                    results.append(ValidationResult.ValidationResultColumn("Error", msg, record_id))
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

    def __init__(self):
        self.rule_sections: Dict[str, RuleSection] = {}

    def add_rule_section(self, rule_section: RuleSection):
        if type(rule_section) is not RuleSection:
            raise TypeError("The rule section parameter must be a RuleSection object")
        section_name = rule_section.get_section_name()
        if section_name in self.rule_sections:
            raise ValueError("Two rule sections use the same name")
        self.rule_sections[section_name] = rule_section

    def get_all_section_names(self) -> List[str]:
        names: List[str] = []
        for key in self.rule_sections.keys():
            names.append(key)
        return names

    def get_section_by_name(self, section_name: str) -> RuleSection:
        if type(section_name) is not str:
            raise TypeError("The section name must be a string")
        if section_name not in self.rule_sections:
            raise ValueError("No section found according to the given name " + section_name)
        return self.rule_sections.get(section_name)

    def validate(self, record: Dict, id_field: str = 'Data source ID') -> ValidationResult.ValidationResultRecord:
        attributes = record['attributes']
        record_id = attributes[id_field][0]['value']
        record_result = ValidationResult.ValidationResultRecord(record_id)

        unmapped = attributes.copy()  # create a copy and remove the ruleset-mapped columns
        del unmapped[id_field]
        for section_name in self.get_all_section_names():
            section_rule = self.get_section_by_name(section_name)
            if section_rule.meet_condition(record):
                section_results = section_rule.validate(attributes, record_id, id_field)
                for one in section_results:
                    record_result.add_validation_result_column(one)

                for field_name in section_rule.get_rule_names():
                    if field_name in unmapped:
                        del unmapped[field_name]
        # unmapped column check can only be done here, not in section rule validation as all section rules need to apply
        if unmapped:
            for key in unmapped.keys():
                record_result.add_validation_result_column(
                    ValidationResult.ValidationResultColumn(
                        "Warning", "Column " + key + " could not be found in ruleset", record_id))
        if record_result.is_empty():
            record_result.add_validation_result_column(
                ValidationResult.ValidationResultColumn("Pass", "", record_id))
        return record_result
