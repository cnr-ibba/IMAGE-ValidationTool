class ValidationResultColumn:
    status_id = -1

    def __init__(self, status, message, record_id):
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

    def __str__(self):
        if self.status_id != 1:
            message = "Record " + self.record_id + ": " + self.status.capitalize()
            message = message + " (" + self.message + ")"
            message = message + " status id " + str(self.status_id)
            return message
        return ""

    def get_message(self):
        if self.status_id == 1:
            return ""
        else:
            return self.status.capitalize() + ": " + self.message + " for Record " + self.record_id


class ValidationResultRecord:
    result_set = []

    def __init__(self, record_id):
        self.record_id = record_id
        self.result_set = []

    def add_validation_result_column(self, result):
        if self.record_id != result.record_id:
            raise ValueError('Record ids do not match, fail to add result for %s to the result set of %s'
                             % (result.record_id, self.record_id))
        self.result_set.append(result)

    def get_overall_status(self):
        result = 1
        for one in self.result_set:
            result = result * one.status_id
        if result == 1:
            return "Pass"
        elif result == 0:
            return "Error"
        else:
            return "Warning"

    def get_specific_result_type(self, status):
        result = []
        for one in self.result_set:
            if one.status == status.lower():
                result.append(one)
        return result

    # inclusive indicates whether include warning message if status is error
    def get_messages(self, inclusive=True):
        status = self.get_overall_status()
        msgs = []
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
    def add_messages(for_return, validation_results):
        for result in validation_results:
            for_return.append(result.get_message())
        return for_return

    def is_empty(self):
        if self.result_set:
            return False
        else:
            return True
