"""
Validation results are represented in three levels
1. field level: the validation result for the field
2. record level: one record has multiple fields, therefore a list of field validation results
3. submission level: using built-in list of record validation records
"""
from typing import List
import logging

logger = logging.getLogger(__name__)


class ValidationResultConstant:
    # errors occurred during ruleset based validation
    RULESET_BASED = "ruleset based"
    # errors occurred during checking ruleset
    RULESET_CHECK = "ruleset check"
    # errors occurred during checking usi representation of data
    USI_CHECK = "usi structure"
    # errors occurred during submitting via USI API (the messages returned from API)
    USI_API = "usi api response"
    # errors occurred during checking relationships (pure relationship,
    # not the attributes values for the related records (context validation)
    RELATIONSHIP = "relationship"
    # errors occurred during context validation
    CONTEXT = "context validation"
    # general errors e.g. IO error
    GENERAL = "general"
    # for pass result
    EMPTY = ""
    # Three defined statuses
    PASS = "Pass"
    WARNING = "Warning"
    ERROR = "Error"


class ValidationResultColumn:
    """
    The validation result for one field
    """
    status_id: int = -1

    def __init__(self, status: str, message: str, record_id: str, field_name: str,
                 source: str = ValidationResultConstant.RULESET_BASED):
        """
        Constructor method
        :param status: status of the validation result, one of pass, warning or error
        :param message: the detail of the warning or error, expected to be empty for pass
        :param record_id: the record id
        :param source: the source of the validation result
        :param field_name: the field name
        """
        if type(status) is not str:
            raise TypeError("Status must be a string")
        if type(message) is not str:
            raise TypeError("Message must be a string")
        if type(record_id) is not str:
            raise TypeError("Record id must be a string")
        if type(field_name) is not str:
            raise TypeError("Field name must be a string")
        if type(source) is not str:
            raise TypeError("Source must be a string")

        self.status = status.lower()
        if self.status == "pass":
            self.status_id = 1
        elif self.status == "error":
            self.status_id = 0
        elif self.status == "warning":
            self.status_id = 2
        else:
            raise ValueError(f'invalid status value {status} which can only be pass, error or warning')
        self.message = message
        self.record_id = record_id
        self.field_name = field_name
        self.source = source

    # self.field_name is contained in the self.message
    def __str__(self) -> str:
        """
        Convert the object into a string
        :return: the message to be displayed on the screen
        """
        if self.status_id != 1:
            if self.source == ValidationResultConstant.RULESET_CHECK:
                return f"{self.status.capitalize()}: {self.message}"
            elif self.source == ValidationResultConstant.USI_CHECK \
                    or self.source == ValidationResultConstant.RELATIONSHIP\
                    or self.source == ValidationResultConstant.GENERAL:
                return self.message
            else:
                return f"{self.status.capitalize()}: {self.message} for Record {self.record_id}"
        return ""

    def get_record_id(self) -> str:
        """
        Get the record id
        :return: record id
        """
        return self.record_id

    def get_field_name(self) -> str:
        """
        Get the field name
        :return: field name
        """
        return self.field_name

    def get_message(self) -> str:
        """
        Get the detail of the validation result, expected to be empty for pass
        :return: message describing the error/warning detail
        """
        if self.status_id == 1:
            return ""
        else:
            return self.message

    def get_status(self) -> str:
        """
        Get the validation status
        :return: validation status
        """
        if self.status_id == 1:
            return ValidationResultConstant.PASS
        elif self.status_id == 0:
            return ValidationResultConstant.ERROR
        else:
            return ValidationResultConstant.WARNING

    def get_source(self) -> str:
        """
        Get the error/warning source, empty if pass
        :return: source of the validation result
        """
        if self.status_id == 1:
            return ValidationResultConstant.EMPTY
        return self.source

    def get_comparable_str(self) -> str:
        """
        Get error/warning message
        :return: message of the result
        """
        if self.status_id != 1:
            return f"{self.status.capitalize()}: {self.message}"
        return ""

    def __eq__(self, other):
        """
        Compare two objects to see whether they are equal
        :param other: another field validation result to be compared with
        :return: True when equal, False otherwise
        """
        if not isinstance(other, ValidationResultColumn):
            return NotImplemented
        if self.status_id == 1 and other.status_id == 1:
            return True
        return self.status_id == other.status_id and self.message == other.message

    def __hash__(self):
        """
        Hash method
        :return:
        """
        if self.status_id == 1:
            return 1
        return hash((self.status_id, self.message))


class ValidationResultRecord:
    """
    The validation result for one record which has one or more fields
    """
    result_set: List[ValidationResultColumn]

    def __init__(self, record_id: str):
        """
        Constructor method
        :param record_id: the record id
        """
        if type(record_id) is not str:
            raise TypeError("Record id must be a string")
        self.record_id = record_id
        self.result_set = []

    def add_validation_result_column(self, result: ValidationResultColumn) -> None:
        """
        Add one field validation result which must have the same record id
        :param result: field validation result
        """
        if type(result) is not ValidationResultColumn:
            raise TypeError("The parameter must be of ValidationResultColumn type")
        if self.record_id != result.record_id:
            raise ValueError('Record ids do not match, fail to add result for %s to the result set of %s'
                             % (result.record_id, self.record_id))
        self.result_set.append(result)

    def get_overall_status(self) -> str:
        """
        Get the status of validation result for the record which is computed from all related field results
        :return: record validation status, one of pass, warning or error
        """
        result = 1
        for one in self.result_set:
            result = result * one.status_id
        if result == 1:
            return ValidationResultConstant.PASS
        elif result == 0:
            return ValidationResultConstant.ERROR
        else:
            return ValidationResultConstant.WARNING

    def get_size(self) -> int:
        """
        Get the number of field validation results
        :return: the size of field results
        """
        return len(self.result_set)

    def get_specific_result_type(self, status: str) -> List[ValidationResultColumn]:
        """
        Get list of field validation results with same status
        :param status: status the results share
        :return: a list of field validation results
        """
        if type(status) is not str:
            raise TypeError("The status parameter must be a string")
        status = status.lower()
        if status != 'pass' and status != 'warning' and status != 'error':
            raise ValueError("status must be one of Pass, Warning, or Error")
        result: List[ValidationResultColumn] = []
        for one in self.result_set:
            if one.status == status:
                result.append(one)
        return result

    # inclusive indicates whether include warning message if status is error
    def get_messages(self, inclusive=True) -> List[str]:
        """
        Get list of error/warning details
        :param inclusive: flag indicate whether to include warning
        :return: list of result details
        """
        if type(inclusive) is not bool:
            raise TypeError("Inclusive parameter must be a boolean value")
        status: str = self.get_overall_status()
        msgs: List[str] = []
        if status == ValidationResultConstant.PASS:
            return []
        elif status == ValidationResultConstant.ERROR:
            msgs = self.add_messages(msgs, self.get_specific_result_type(ValidationResultConstant.ERROR))
            if inclusive:
                msgs = self.add_messages(msgs, self.get_specific_result_type(ValidationResultConstant.WARNING))
        else:
            msgs = self.add_messages(msgs, self.get_specific_result_type(ValidationResultConstant.WARNING))
        return msgs

    @staticmethod
    def add_messages(for_return: List[str], validation_results: List[ValidationResultColumn]):
        """
        Add details of field validation results
        :param for_return: message list
        :param validation_results: list of field validation results
        :return: updated message list
        """
        for result in validation_results:
            for_return.append(str(result))
        return for_return

    def is_empty(self) -> bool:
        """
        Check whether there is error/warning validation return
        :return: Yes when the list of field validation results is empty
        """
        if self.result_set:
            return False
        else:
            return True
