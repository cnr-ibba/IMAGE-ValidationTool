from typing import List
import logging

logger = logging.getLogger(__name__)


class ValidationResultColumn:
    status_id: int = -1

    def __init__(self, status: str, message: str, record_id: str, field_name: str):
        if type(status) is not str:
            raise TypeError("Status must be a string")
        if type(message) is not str:
            raise TypeError("Message must be a string")
        if type(record_id) is not str:
            raise TypeError("Record id must be a string")
        if type(field_name) is not str:
            raise TypeError("Field name must be a string")

        self.status = status.lower()
        if self.status == "pass":
            self.status_id = 1
        elif self.status == "error":
            self.status_id = 0
        elif self.status == "warning":
            self.status_id = 2
        else:
            raise ValueError('invalid status value %s which can only be pass, error or warning' % status)
        self.message = message
        self.record_id = record_id
        self.field_name = field_name

    # self.field_name is contained in the self.message
    def __str__(self) -> str:
        if self.status_id != 1:
            return f"{self.status.capitalize()}: {self.message} for Record {self.record_id}"
        return ""

    def get_record_id(self):
        return self.record_id

    def get_field_name(self):
        return self.field_name

    def get_message(self) -> str:
        if self.status_id == 1:
            return ""
        else:
            return self.message

    def get_status(self) -> str:
        if self.status_id == 1:
            return "Pass"
        elif self.status_id == 0:
            return "Error"
        else:
            return "Warning"

    def get_comparable_str(self) -> str:
        if self.status_id != 1:
            return f"{self.status.capitalize()}: {self.message}"
        return ""

    def __eq__(self, other):
        if not isinstance(other, ValidationResultColumn):
            return NotImplemented
        if self.status_id == 1 and other.status_id == 1:
            return True
        return self.status_id == other.status_id and self.message == other.message

    def __hash__(self):
        if self.status_id == 1:
            return 1
        return hash((self.status_id, self.message))


class ValidationResultRecord:
    result_set: List[ValidationResultColumn]

    def __init__(self, record_id: str):
        if type(record_id) is not str:
            raise TypeError("Record id must be a string")
        self.record_id = record_id
        self.result_set = []

    def add_validation_result_column(self, result: ValidationResultColumn) -> None:
        if type(result) is not ValidationResultColumn:
            raise TypeError("The parameter must be of ValidationResultColumn type")
        if self.record_id != result.record_id:
            raise ValueError('Record ids do not match, fail to add result for %s to the result set of %s'
                             % (result.record_id, self.record_id))
        self.result_set.append(result)

    def get_overall_status(self) -> str:
        result = 1
        for one in self.result_set:
            result = result * one.status_id
        if result == 1:
            return "Pass"
        elif result == 0:
            return "Error"
        else:
            return "Warning"

    def get_size(self) -> int:
        return len(self.result_set)

    def get_specific_result_type(self, status: str) -> List[ValidationResultColumn]:
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
        if type(inclusive) is not bool:
            raise TypeError("Inclusive parameter must be a boolean value")
        status: str = self.get_overall_status()
        msgs: List[str] = []
        if status == "Pass":
            return []
        elif status == "Error":
            msgs = self.add_messages(msgs, self.get_specific_result_type("Error"))
            if inclusive:
                msgs = self.add_messages(msgs, self.get_specific_result_type("Warning"))
        else:
            msgs = self.add_messages(msgs, self.get_specific_result_type("Warning"))
        return msgs

    @staticmethod
    def add_messages(for_return: List[str], validation_results: List[ValidationResultColumn]):
        for result in validation_results:
            for_return.append(str(result))
        return for_return

    def is_empty(self) -> bool:
        if self.result_set:
            return False
        else:
            return True
