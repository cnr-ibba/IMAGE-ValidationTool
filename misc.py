import re
import datetime
import dateutil.parser


def get_today() -> str:
    now = datetime.datetime.now().isoformat()
    return str(now)[:10]


def to_lower_camel_case(input_str: str) -> str:
    input_str = input_str.replace("_", " ")
    components = input_str.split(' ')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].lower() + ''.join(x.title() for x in components[1:])


def from_lower_camel_case(lower_camel: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', lower_camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).lower()


# IRI syntax http://www.ietf.org/rfc/rfc3987.txt
# in this case, start with http
# assume always followed by purl.obolibrary.org except for EFO ontology
def is_IRI(term: str) -> bool:
    pattern_general = re.compile("^https?:\/\/purl\.obolibrary\.org\/obo\/")
    pattern_efo = re.compile("^https?:\/\/www\.ebi\.ac\.uk\/efo\/")
    if pattern_general.match(term) or pattern_efo.match(term):
        return True
    else:
        return False


def is_email(email: str, only:bool =False) -> bool:
    pattern = re.compile(
        "(?:[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])")
    if only:
        pattern = re.compile(
            "^(?:[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$")
    m = re.search(pattern, email)
    if m:
        return True
    return False


def is_uri(uri: str) -> bool:
    # https://stackoverflow.com/questions/161738/what-is-the-best-regular-expression-to-check-if-a-string-is-a-valid-url
    pattern = re.compile(
        "((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+(:[0-9]+)?|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.-_\w]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)")
    m = re.search(pattern, uri)
    if m:
        return True
    return False


# https://www.doi.org/doi_handbook/2_Numbering.html#2.2
def is_doi(doi: str) -> bool:
    # prefix suffix separated by /, so split and expect two elements
    parts = doi.split('/')
    if len(parts) != 2:
        return False
    pattern = re.compile("^(doi:)?10\.(\d{4,})(\.\d+)?$")
    # group(1) could be None
    m = re.search(pattern, parts[0])
    if m:
        if int(m.group(2)) < 1000: # the number starts from 1000
            return False
        return True
    else:
        return False


# date_format is validated in the allowed value of units
def is_date_match_format(date: str, date_format: str) -> str:
    not_matched_str = "The date value " + date + " does not match to the format " + date_format
    if len(date) != len(date_format):
        return not_matched_str
    elmts_date = date.split("-")
    elmts_format = date_format.split("-")
    if len(elmts_date) != len(elmts_format):
        return not_matched_str
    for i, val in enumerate(elmts_date):
        elmt_format = elmts_format[i]
        if len(val) != len(elmt_format):
            return not_matched_str
    try:
        dateutil.parser.parse(date, yearfirst=True)
    except ValueError:
        return "Unrecognized date value " + date
    return ""


def test_to_lower_camel_case() -> None:
    arr = {"country", "Disease", "Physiological status", "test__string", "test _1"}
    for i in arr:
        print(i)
        val = to_lower_camel_case(i)
        print(val)
        val = from_lower_camel_case(val)
        print(val)
        print()


def extract_ontology_id_from_iri(url: str) -> str:
    if url.find('/'):
        elmts = url.split('/')
        return elmts[-1]
    else:
        return url

