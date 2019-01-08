import requests
# import json
from misc import *


def use_zooma(term, category):
    new_term = term.replace(" ", "+")
    # main production server
    host = "https://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate?propertyValue=" + new_term
    # test zooma server
    # host = "http://snarf.ebi.ac.uk:8480/spot/zooma/v2/api/services/annotate?propertyValue="+newTerm
    # add filter: configure datasource and ols libraries
    category = from_lower_camel_case(category)
    if category == "species":  # necessary if
        category = "organism"
        host += "&filter=required:[ena],ontologies:[NCBITaxon]"  # species, only search NCBI taxonomy ontology
    elif category == "breed":
        host += "&filter=required:[ena],ontologies:[lbo]"  # breed, only search Livestock Breed Ontology
    elif category == "country" or category == "geneBankCountry":
        host += "&filter=required:[ena],ontologies:[ncit,gaz]"  # country, only search NCIT Ontology
    else:
        host += "&filter=required:[ena],ontologies:[efo,uberon,obi,pato]"  # according to IMAGE ruleset, only these ontology libraries are allowed in the ruleset, so not search others, gaz is for countries
    high_result = {}
    good_result = {}
    result = {}
    # print (host)
    # host = "https://github.com/timeline.json"
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
            # else: #medium/low

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


def get_general_breed_by_species(species, cross=False):
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
    return ontology


def is_child_of(child, parent):
    child = convert_to_iri(child)
    parent = convert_to_iri(parent)
    host = "https://www.ebi.ac.uk/ols/api/search?q=" + child + "&queryFields=iri&childrenOf=" + parent
    # print (host)
    request = requests.get(host)
    response = request.json()
    # print (json.dumps(response['response'], indent=4, sort_keys=True))
    num_found = response['response']['numFound']
    if num_found == 0:
        return False
    else:
        return True


def is_leaf(term_iri):
    short_term = extract_ontology_id_from_iri(term_iri)
    ontology = get_ontology_library(short_term)
    host = "https://www.ebi.ac.uk/ols/api/ontologies/" + ontology + "/terms?iri=" + term_iri
    request = requests.get(host)
    response = request.json()
    has_children = response['_embedded']['terms'][0]['has_children']
    return not has_children


def get_ontology_library(short_term):
    return short_term.split("_")[0]


def convert_to_iri(term):
    if is_IRI(term):
        return term
    else:
        # as not iri, assuming to be short term
        library = get_ontology_library(term)
        if library.lower() == "efo":
            return 'http://www.ebi.ac.uk/efo/' + term
        else:
            return 'http://purl.obolibrary.org/obo/' + term


def testZooma():
    # annotation = useZooma('mus musculus','species')  	#organism in gxa datasource with high, disallow any datasource, good
    # annotation = useZooma('deutschland','country')		#country type=null, two matches medium/low, so returned value is None
    # annotation = useZooma('norway','country')		#country type=null, while using ena datasource, high
    # annotation = useZooma('bentheim black pied','breed')	#breed LBO_0000347	type=null, good
    # annotation = useZooma('Bunte Bentheimer','breed')	#breed LBO_0000436	type=null, good

    # annotation = useZooma('normal','disease')		#Health status	type=disease
    # annotation = useZooma('spleen','organism part')		#Organism part
    # annotation = useZooma('semen','organism part')		#Organism part UBERON_0001968 (semen) medium for default OLS setting, good for specifying ontologies to search against
    # annotation = useZooma('adult','developmental stage')		#Development stage type=developmental stage EFO_0001272 (adult)
    # annotation = useZooma('mature','physiological stage')		#Physiological stage several medium/low none of them related to physiological stage PATO_0001701 (mature)

    # annotation = useZooma('turkey','species')
    annotation = use_zooma('Poitevine', 'breed')  # without limiting to LBO, match to a random GAZ term
    print(annotation)

