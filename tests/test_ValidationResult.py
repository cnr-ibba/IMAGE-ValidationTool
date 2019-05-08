import unittest

from image_validation import ValidationResult


class TestValidationResult(unittest.TestCase):
    column_pass = ValidationResult.ValidationResultColumn('pass', 'redundant', 'sample_1', 'id')
    column_warning = ValidationResult.ValidationResultColumn('Warning', 'term not match', 'sample_1', 'id')
    column_warning_2 = ValidationResult.ValidationResultColumn(
        'Warning', 'recommended to have value for field a', 'sample_2', 'id')
    column_error = ValidationResult.ValidationResultColumn(
        'ERROR', 'value used in field b is not allowed', 'sample_1', 'error field')

    def test_ValidationResultColumn_types(self):
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 12, 'message', 'record id', 'field name')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, -12.34, 'message', 'record id', 'field')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, True, 'message', 'record id', 'field')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', 12, 'record id', 'field name')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', -12.34, 'record id', 'field name')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', False, 'record id', 'field name')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', 'message', 12, 'field name')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', 'message', -12.34, 'field name')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', 'message', True, 'field name')
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', 'message', 'record', 12)
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', 'message', 'record', -12.34)
        self.assertRaises(TypeError, ValidationResult.ValidationResultColumn, 'pass', 'message', 'record', True)

    # test status must be one of three options
    def test_ValidationResultColumn_values(self):
        self.assertRaises(ValueError, ValidationResult.ValidationResultColumn,
                          'something', 'another thing', 'record', 'field')

    def test_str(self):
        self.assertEqual(str(self.column_pass), "")
        self.assertEqual(str(self.column_warning_2),
                         "Warning: recommended to have value for field a for Record sample_2")
        self.assertEqual(str(self.column_error), "Error: value used in field b is not allowed for Record sample_1")

    def test_get_record_id(self):
        self.assertEqual(self.column_pass.get_record_id(), "sample_1")
        self.assertEqual(self.column_warning_2.get_record_id(), "sample_2")
        self.assertEqual(self.column_error.get_record_id(), "sample_1")

    def test_get_field_name(self):
        self.assertEqual(self.column_pass.get_field_name(), "id")
        self.assertNotEqual(self.column_warning.get_field_name(), "warning")
        self.assertEqual(self.column_error.get_field_name(), "error field")

    def test_get_message(self):
        self.assertEqual(self.column_pass.get_message(), "")
        self.assertEqual(self.column_warning.get_message(), "term not match")
        self.assertEqual(self.column_warning_2.get_message(), "recommended to have value for field a")
        self.assertEqual(self.column_error.get_message(), "value used in field b is not allowed")

    def test_get_status(self):
        self.assertEqual(self.column_pass.get_status(), "Pass")
        self.assertEqual(self.column_warning.get_status(), "Warning")
        self.assertEqual(self.column_error.get_status(), "Error")

    def test_equal_ValidationResultColumn(self):
        self.assertNotEqual(self.column_pass, self.column_error)
        self.assertEqual(self.column_pass,
                         ValidationResult.ValidationResultColumn("pass", "message", "record", "field"))
        # different sample id, different field name, message same => equal
        self.assertEqual(self.column_error,
                         ValidationResult.ValidationResultColumn(
                             'ERROR', 'value used in field b is not allowed', 'sample_2', 'error field 2'))

    def test_equal_ValidationResultColumn_type(self):
        self.assertNotEqual(self.column_pass, 'pass')

    def test_hash_ValidationResultColumn(self):
        self.assertEqual(hash(self.column_pass), 1)
        self.assertNotEqual(hash(self.column_error), hash('error'))
        self.assertNotEqual(hash(self.column_error), hash(self.column_error.message))

    def test_ValidationResultRecord(self):
        self.assertRaises(TypeError, ValidationResult.ValidationResultRecord, 12)
        self.assertRaises(TypeError, ValidationResult.ValidationResultRecord, -12.34)
        self.assertRaises(TypeError, ValidationResult.ValidationResultRecord, True)

    # also test is_empty function
    def test_add_validation_result_column(self):
        collection = ValidationResult.ValidationResultRecord('sample_1')
        self.assertTrue(collection.is_empty())
        self.assertRaises(ValueError, collection.add_validation_result_column, self.column_warning_2)
        collection.add_validation_result_column(self.column_warning)
        self.assertEqual(collection.get_size(), 1)
        self.assertFalse(collection.is_empty())

    def test_add_validation_result_column_types(self):
        collection = ValidationResult.ValidationResultRecord('sample_1')
        self.assertRaises(TypeError, collection.add_validation_result_column, "string")
        self.assertRaises(TypeError, collection.add_validation_result_column, 12)

    def test_get_overall_status(self):
        collection = ValidationResult.ValidationResultRecord('sample_1')
        # empty thus pass
        self.assertEqual(collection.get_overall_status(), "Pass")
        collection.add_validation_result_column(self.column_warning)
        self.assertRaises(ValueError, collection.add_validation_result_column, self.column_warning_2)
        # warning added in the test above
        self.assertEqual(collection.get_overall_status(), "Warning")
        # add pass
        collection.add_validation_result_column(self.column_pass)
        self.assertEqual(collection.get_overall_status(), "Warning")
        # add error
        collection.add_validation_result_column(self.column_error)
        self.assertEqual(collection.get_overall_status(), "Error")
        self.assertEqual(collection.get_size(), 3)

    def test_get_specific_result_type(self):
        collection = ValidationResult.ValidationResultRecord('sample_1')
        self.assertRaises(TypeError, collection.get_specific_result_type, 12)
        self.assertRaises(TypeError, collection.get_specific_result_type, -12.34)
        self.assertRaises(TypeError, collection.get_specific_result_type, True)
        self.assertRaises(ValueError, collection.get_specific_result_type, 'wrong')

    def test_get_messages(self):
        collection = ValidationResult.ValidationResultRecord('sample_1')
        self.assertRaises(TypeError, collection.get_messages, 12)
        self.assertRaises(TypeError, collection.get_messages, '12')
        # test pass status, expected empty
        collection.add_validation_result_column(self.column_pass)
        self.assertListEqual(collection.get_messages(), [])

        # test warning status
        collection.add_validation_result_column(self.column_warning)
        expected_warning = ['Warning: term not match for Record sample_1']
        self.assertListEqual(collection.get_messages(), expected_warning)

        collection.add_validation_result_column(self.column_error)
        expected_error_only = ["Error: value used in field b is not allowed for Record sample_1"]
        self.assertListEqual(collection.get_messages(False), expected_error_only)
        expected_include_warning = expected_error_only
        expected_include_warning.append('Warning: term not match for Record sample_1')
        self.assertListEqual(collection.get_messages(), expected_include_warning)


if __name__ == '__main__':
    unittest.main()
