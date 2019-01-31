import logging
import validation
from typing import List, Dict

logger = logging.getLogger(__name__)


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
            raise ValueError("The provided value "+required+" is not one of "+", ".join(RuleField.allowed_required))
        if field_type not in RuleField.allowed_type:
            raise ValueError("The provided value "+field_type+" is not one of "+", ".join(RuleField.allowed_type))
        if multiple not in RuleField.allowed_multiple:
            raise ValueError("The provided value "+multiple+" is not one of "+", ".join(RuleField.allowed_multiple))

        self.name: str = name
        self.type: str = field_type
        self.required: str = required
        self.multiple: bool = False
        multiple = multiple.lower()
        if multiple == 'yes' or multiple == 'max 2':
            self.multiple = True
        elif multiple != 'no':
            raise ValueError('Unrecognized allow multiple value '+multiple+" which can only be yes, no, or max 2")
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

    def get_allow_multiple(self) -> bool:
        return self.multiple


class RuleSection:

    def __init__(self, section_name: str):
        self.name = section_name
        self.rules: Dict[str, Dict[str, RuleField]] = {}
        self.conditions: Dict[str, str] = {}
        self.rule_names: Dict[str, int] = {}

    def add_rule(self, rule: RuleField):
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

    def get_section_name(self):
        return self.name


class RuleSet:

    def __init__(self):
        self.rule_sections: Dict[str, RuleSection] = {}

    def add_rule_section(self, rule_section: RuleSection):
        section_name = rule_section.get_section_name()
        if section_name in self.rule_sections:
            raise KeyError("Two rule sections use the same name")
        self.rule_sections[section_name] = rule_section

    def get_all_section_names(self):
        return self.rule_sections.keys()

    def get_section_by_name(self, section_name: str) -> RuleSection:
        if section_name not in self.rule_sections:
            raise ValueError("No section found according to the given name "+section_name)
        return self.rule_sections.get(section_name)






