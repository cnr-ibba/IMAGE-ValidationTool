import requests
import logging
from . import misc
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


# search against zooma and return the matched ontology
def use_zooma(term: str, category: str) -> Dict[str, str]:
    if type(term) is not str:
        raise TypeError("The method only take string for term parameter")
    if type(category) is not str:
        raise TypeError("The method only take string for category parameter")
    new_term = term.replace(" ", "+")
    # main production server
    host = "https://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate?propertyValue=" + new_term
    logger.debug(host)
    # test zooma server
    # host = "http://snarf.ebi.ac.uk:8480/spot/zooma/v2/api/services/annotate?propertyValue="+newTerm
    # add filter: configure datasource and ols libraries
    category = misc.from_lower_camel_case(category)
    if category == "species":  # necessary if
        category = "organism"
        host += "&filter=required:[ena],ontologies:[NCBITaxon]"  # species, only search NCBI taxonomy ontology
    elif category == "breed":
        host += "&filter=required:[ena],ontologies:[lbo]"  # breed, only search Livestock Breed Ontology
    elif category == "country" or category == "gene bank country":
        host += "&filter=required:[ena],ontologies:[ncit]"  # country, only search NCIT Ontology
    elif category == "organism part":
        host += "&filter=required:[ena],ontologies:[pato]"  # country, only search NCIT Ontology
    else:
        # according to IMAGE ruleset, only these ontology libraries are allowed in the ruleset,
        # so not search others
        host += "&filter=required:[ena],ontologies:[efo,uberon,obi,pato]"
    high_result = {}
    good_result = {}
    result = {}
    request = requests.get(host)
    # print (json.dumps(request.json(), indent=4, sort_keys=True))
    for elem in request.json():
        detected_type = elem['annotatedProperty']['propertyType']
        # the type must match the given one or be null
        if detected_type is None or detected_type == category:
            confidence = elem['confidence'].lower()
            property_value = elem['annotatedProperty']['propertyValue']
            semantic_tag = elem['_links']['olslinks'][0]['semanticTag']
            # potential useful data: ['_links']['olslinks'][0]['href']:
            # "https://www.ebi.ac.uk/ols/api/terms?iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FUBERON_0002106"
            if confidence == "high":
                high_result[property_value] = semantic_tag
            elif confidence == "good":
                good_result[property_value] = semantic_tag
            else:  # medium/low
                pass

    # print(high_result)
    # print(good_result)
    result['type'] = category
    if high_result:
        result['confidence'] = 'High'
        for value in high_result:
            result['text'] = value
            result['ontologyTerms'] = high_result[value]
            return result

    if good_result:
        result['confidence'] = 'Good'
        for value in good_result:
            result['text'] = value
            result['ontologyTerms'] = good_result[value]
            return result


def get_general_breed_by_species(species: str, cross: bool = False) -> Dict[str, str]:
    logger.debug("species: "+species+" is crossbreed:"+str(cross))
    if type(species) is not str:
        raise TypeError("The method only take string for species parameter")
    if type(cross) is not bool:
        raise TypeError("The method only take boolean value for cross parameter")
    species = species.lower()
    ontology = {}
    if species == 'bos taurus':
        if cross:
            ontology['text'] = 'Cattle crossbreed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0001036'
        else:
            ontology['text'] = 'cattle breed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0000001'
    elif species == 'gallus gallus':
        if cross:
            ontology['text'] = 'Chicken crossbreed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0001037'
        else:
            ontology['text'] = 'chicken breed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0000002'
    elif species == 'equus caballus':
        if cross:
            ontology['text'] = 'Horse crossbreed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0001039'
        else:
            ontology['text'] = 'horse breed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0000713'
    elif species == 'sus scrofa':
        if cross:
            ontology['text'] = 'Pig crossbreed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0001040'
        else:
            ontology['text'] = 'pig breed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0000003'
    elif species == 'ovis aries':
        if cross:
            ontology['text'] = 'Sheep crossbreed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0001041'
        else:
            ontology['text'] = 'sheep breed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0000004'
    elif species == 'capra hircus':
        if cross:
            ontology['text'] = 'Goat crossbreed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0001038'
        else:
            ontology['text'] = 'goat breed'
            ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0000954'
    elif species == 'bubalus bubalis':
        ontology['text'] = 'buffalo breed'
        ontology['ontologyTerms'] = 'http://purl.obolibrary.org/obo/LBO_0001042'
    else:
        return None
    return ontology


class Ontology:
    found: bool = False

    # According to Simon's reply in ols-support #317084
    # It is best if you have the IRI. but the short id is highly likely to be unique too
    # so you are safe to lookup on the /terms endpoint using the short id.
    # You just have to be aware that the response will be a list and
    # you may have the same id approving in multiple ontologies
    # So you need to look for the term with "is_defining_ontology : true”
    # to find the description of the term in the source ontology.
    # e.g. https://www.ebi.ac.uk/ols/api/terms?id=UBERON_0001037 has 12 entries,
    # the 3rd in the list is has is_defining_ontology : true and that is the correct term in Uberon.
    def __init__(self, short_term: str):
        self.short_term = short_term
        host = "http://www.ebi.ac.uk/ols/api/terms?id=" + short_term
        request = requests.get(host)
        response = request.json()
        num = response['page']['totalElements']

        if num:
            if num > 20:
                host = host + "&size=" + str(num)
                request = requests.get(host)
                response = request.json()
            terms = response['_embedded']['terms']
            for term in terms:
                if term['is_defining_ontology']:
                    self.found = True
                    self.detail = term
        else:
            logger.error("Could not find information for " + short_term)

    def __eq__(self, other):
        return self.get_short_term() == other.get_short_term()

    def get_short_term(self)->str:
        if not self.found:
            logger.warning("No ontology found on OLS, just return the given short term")
        return self.short_term

    def get_ontology_name(self) -> str:
        if self.found:
            return self.detail['ontology_name']
        else:
            logger.warning("Return empty for ontology name as fail to find ontology on OLS for term "+self.short_term)
            return ""

    def get_iri(self) -> str:
        if self.found:
            return self.detail['iri']
        else:
            logger.warning("Return empty for iri as fail to find ontology on OLS for term "+self.short_term)
            return ""

    def get_label(self) -> str:
        if self.found:
            return self.detail['label']
        else:
            logger.warning("Return empty for label as fail to find ontology on OLS for term "+self.short_term)
            return ""

    def is_leaf(self) -> bool:
        if self.found:
            return not self.detail['has_children']

    def get_labels_and_synonyms(self) -> List[str]:
        result: List[str] = []
        if self.found:
            result.append(self.get_label())
            if 'synonyms' in self.detail and self.detail['synonyms']:
                for synonym in self.detail['synonyms']:
                    result.append(synonym)
        return result

    # check whether provided label appears in the provided ontology label and synonyms
    def label_match_ontology(self, label: str, case_sensitive: bool = True) -> bool:
        if type(label) is not str:
            raise TypeError("The method only take string for label parameter")
        if type(case_sensitive) is not bool:
            raise TypeError("The method only take boolean for case_sensitive parameter "
                            "which is optional and defaulted to be true")
        online_labels = self.get_labels_and_synonyms()
        if not case_sensitive:
            label = label.lower()
        for current in online_labels:
            if not case_sensitive:
                current = current.lower()
            if label == current:
                return True
        return False


class OntologyCache:
    cache: Dict[str, Ontology]
    children_checked: Dict[str, Dict[str, bool]] = {}
    # parents_checked: Dict[str, Dict[str, bool]] = {}

    def __init__(self):
        self.cache = {}
        logger.debug("Initializing ontology cache")

    def contains(self, short_term: str)->bool:
        if type(short_term) is not str:
            raise TypeError("The method only take string as its input")
        return short_term in self.cache

    def add_ontology(self, ontology: Ontology) -> None:
        if type(ontology) is not Ontology:
            raise TypeError("The method only take Ontology type as its input")
        short_term = ontology.get_short_term()
        self.cache[short_term] = ontology
        if short_term not in self.children_checked:
            self.children_checked[short_term] = {}

    def get_ontology(self, short_term: str) -> Ontology:
        if type(short_term) is not str:
            raise TypeError("The method only take string as its input")
        if short_term in self.cache:
            logger.debug("load from cache "+short_term)
            return self.cache[short_term]
        else:
            logger.debug("OLS search for new term "+short_term)
            ontology = Ontology(short_term)
            self.add_ontology(ontology)
            logger.debug("Save the new ontology into cache")
            return ontology

    # the method should not be here, but have not got a solution to retrieve ontology from cache
    # while not wanting to maintain checked parent-children relationship
    def has_parent(self, child_term: str, parent_term: str)->bool:
        if type(child_term) is not str:
            raise TypeError("The method only take string as child term parameter")
        if type(parent_term) is not str:
            raise TypeError("The method only take string as parent term parameter")

        if child_term not in self.children_checked:
            self.add_ontology(Ontology(child_term))
        if parent_term not in self.children_checked[child_term]:
            child_detail = self.get_ontology(child_term)
            parent_detail = self.get_ontology(parent_term)
            host = "https://www.ebi.ac.uk/ols/api/search?q=" + child_detail.get_iri()\
                   + "&queryFields=iri&childrenOf=" + parent_detail.get_iri()
            # print (host)
            request = requests.get(host)
            response = request.json()
            # print (json.dumps(response['response'], indent=4, sort_keys=True))
            num_found = response['response']['numFound']

            if num_found == 0:
                self.children_checked[child_term][parent_term] = False
            else:
                self.children_checked[child_term][parent_term] = True

        return self.children_checked[child_term][parent_term]
