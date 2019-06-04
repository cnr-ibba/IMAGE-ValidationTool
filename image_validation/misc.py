import re
import datetime
import dateutil.parser


def get_today() -> str:
    """
    :return: today's date in the format of YYYY-MM-DD
    """
    now = datetime.datetime.now().isoformat()
    return str(now)[:10]


def to_lower_camel_case(input_str: str) -> str:
    """
    This function will convert any string with spaces or underscores to lower camel case string
    :param input_str: target string
    :return: converted string
    """
    if type(input_str) is not str:
        raise TypeError("The method only take str as its input")
    input_str = input_str.replace("_", " ")
    components = input_str.split(' ')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].lower() + ''.join(x.title() for x in components[1:])


def from_lower_camel_case(lower_camel: str) -> str:
    """
    This function will convert 'lowerCamelCase' to 'lower camel case'
    :param lower_camel: string to convert
    :return: return converted string
    """
    if type(lower_camel) is not str:
        raise TypeError("The method only take str as its input")
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', lower_camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).lower()


# https://www.regular-expressions.info/email.html
# more sophisticated case below, probably over kill
# https://stackoverflow.com/questions/201323/how-to-validate-an-email-address-using-a-regular-expression
def is_email(email: str, only: bool = False) -> bool:
    """
    check whether a string is a valid email address
    :param email: the string to be checked
    :param only: indicate whether to allow mailto: at the beginning
    :return: True if a valid email, False otherwise
    """
    if type(email) is not str:
        raise TypeError("The method only take str as its first input")
    # pattern = re.compile(
    # "(?:[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])")
    # if only:
    # pattern = re.compile(
    # "^(?:[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$")
    pattern = re.compile(r"^(mailto:)?[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")
    if only:
        pattern = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")
    m = re.search(pattern, email.lower())
    if m:
        return True
    return False


def is_uri(uri: str) -> bool:
    """
    check whether a string is a valid URI
    :param uri: the string to be checked
    :return: True if a valid URI, False otherwise
    """
    if type(uri) is not str:
        raise TypeError("The method only take str as its input")
    # https://stackoverflow.com/questions/161738/what-is-the-best-regular-expression-to-check-if-a-string-is-a-valid-url
    pattern = re.compile(
        r"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+(:[0-9]+)?|(?:www.|[-;:&=\+\$,\w]+@)"
        r"[A-Za-z0-9.-]+)((?:\/[\+~%\/.-_\w]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)")
    m = re.search(pattern, uri)
    if m:
        return True
    return False


# https://www.doi.org/doi_handbook/2_Numbering.html#2.2
def is_doi(doi: str) -> bool:
    """
    check whether a string is a valid DOI
    :param doi: the string to be checked
    :return: True if a valid DOI, False otherwise
    """
    if type(doi) is not str:
        raise TypeError("The method only takes str as its input")
    # prefix suffix separated by /, so split and expect two elements
    parts = doi.split('/')
    if len(parts) != 2:
        return False
    # the number after "10." starts from 1000, so \d{4,}
    pattern = re.compile(r"^(doi:)?10\.(\d{4,})(\.\d+)?$")
    # group(1) could be None
    m = re.search(pattern, parts[0])
    if m:
        return True
    else:
        return False


def is_biosample_record(accession: str) -> bool:
    """
    check whether the accession is a valid BioSamples accession
    :param accession: the accession to be checked
    :return: True when it is BioSamples accession
    """
    if type(accession) is not str:
        raise TypeError("The method only takes str as its input")
    pattern = re.compile(r"^SAM(N|D|EA)\d+$")
    m = re.search(pattern, accession)
    if m:
        return True
    else:
        return False


# date_format is validated in the allowed value of units
def get_matched_date(date: str, date_format: str) -> str:
    """
    Check whether the date string matches the date format.
    Be aware, the format can only be one of YYYY-MM-DD, YYYY-MM, or YYYY
    :param date: the date string
    :param date_format: the date format, e.g. YYYY-MM-DD
    :return: empty string if matched, otherwise error message
    """
    if type(date) is not str:
        raise TypeError("The method only take str as its first input")
    if type(date_format) is not str:
        raise TypeError("The method only take str as its second input")
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


def extract_ontology_id_from_iri(url: str) -> str:
    """
    Get the ontology short term from iri string
    :param url: iri of ontology
    :return: short term of ontology
    """
    if type(url) is not str:
        raise TypeError("The method only take str as its input")
    if url.find('/') > -1:
        elmts = url.split('/')
        return elmts[-1]
    else:
        return url
