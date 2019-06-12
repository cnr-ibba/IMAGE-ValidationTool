from . import validation, Ruleset
from image_validation.ValidationResult import ValidationResultConstant as VRConstants
from image_validation.ValidationResult import ValidationResultColumn as VRC
from image_validation.ValidationResult import ValidationResultRecord as VRR
from typing import List, Dict
import json
import logging
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s\t%(levelname)s:\t%(name)s line %(lineno)s\t%(message)s',
    level=logging.INFO)


class Submission:
    """
    The class encapsulate complex logics to provide simplified interface of using this module
    """
    def __init__(self, title, id_field: str = "Data source ID"):
        """
        Constructor method
        :param title: the title of submission
        :param id_field: optional, specifies the name of the field in the attribute
        list which is used to identify records
        """
        self.title: str = title
        self.validation_results: Dict[str, VRR] = dict()
        self.data: Dict = None
        self.data_ready_flag: bool = False
        self.ruleset: Ruleset.RuleSet = None
        self.ruleset_pass_flag: bool = False
        self.id_field: str = id_field
        # self.general_errors = ValidationResult.ValidationResultRecord("general")

    def load_data(self, data_file: str, section: str = '') -> VRR:
        """
        Load the data from JSON file which is to be validated and
        do preliminary validation (usi structure and duplicate), if successful set data ready flag
        The preliminary validation results are stored in the general_errors class field
        :param data_file: the JSON file contains the data
        :param section: optional, the name of the section which contains data
        """
        self.data_ready_flag = False
        general_errors = VRR("general")
        try:
            with open(data_file) as infile:
                self.data = json.load(infile)
        except FileNotFoundError:
            msg = f"Could not find the file {data_file}"
            general_errors.add_validation_result_column(
                VRC(VRConstants.ERROR, msg, general_errors.record_id, "", VRConstants.GENERAL))
            return general_errors
        except json.decoder.JSONDecodeError:
            msg = f"The provided file {data_file} is not a valid JSON file."
            general_errors.add_validation_result_column(
                VRC(VRConstants.ERROR, msg, general_errors.record_id, "", VRConstants.GENERAL))
            return general_errors
        if len(section) > 0:
            if section in self.data:
                self.data = self.data[section]
        # check usi structure
        usi_check_result = validation.check_usi_structure(self.data)
        if usi_check_result.get_overall_status() != "Pass":
            return usi_check_result
        # check duplicate id
        msgs = validation.check_duplicates(self.data, self.id_field)
        if msgs:
            for msg in msgs:
                # classify the error as ruleset based error
                # as it is implicitly required that id field holds unique values
                general_errors.add_validation_result_column(
                    VRC(VRConstants.ERROR, msg, general_errors.record_id, self.id_field, VRConstants.RELATIONSHIP))
            return general_errors
        logger.info("All sample records have unique data source ids")
        self.data_ready_flag = True
        return general_errors

    def load_ruleset(self, ruleset_file: str) -> VRR:
        """
        Load the ruleset from the JSON file and check the integrity of the ruleset,
        if successful, set ruleset ready flag
        if not, the results are stored in the class field general_errors
        :param ruleset_file: the JSON file containing the ruleset
        """
        self.ruleset_pass_flag = False
        general_errors = VRR("general")
        try:
            self.ruleset = validation.read_in_ruleset(ruleset_file)
        except KeyError as e:
            general_errors.add_validation_result_column(
                VRC(VRConstants.ERROR, str(e), general_errors.record_id, "", VRConstants.GENERAL))
            return general_errors
        ruleset_check_result: VRR = validation.check_ruleset(self.ruleset)
        if ruleset_check_result.get_overall_status() != "Pass":
            return ruleset_check_result
        logger.info("Ruleset loaded")
        self.ruleset_pass_flag = True
        return general_errors

    def validate(self) -> None:
        """
        Validate the data against the ruleset
        the data needs to be scanned twice, first time to validate individual field in every record based on the ruleset
        second time to validate anything involving with more than one record e.g. relationships and context validation
        or more than one fields in the same record
        The validation result is stored in the object's validation_results field
        """
        # check whether ready to carry out validation
        if not self.data_ready_flag:
            logger.error("The data is not ready, abort the validation proecess")
            return
        if not self.ruleset_pass_flag:
            logger.error("The ruleset is not ready, abort the validation proecess")
            return
        # first scan
        # meanwhile split data according to material type for relationship checking
        data_by_material: Dict[str, Dict[str, Dict]] = {}
        for record in self.data:
            logger.info("Validate record " + record['alias'])
            record_result = self.ruleset.validate(record)
            self.validation_results[record['alias']] = record_result
            try:
                material = record['attributes']['Material'][0]['value'].lower()
                data_by_material.setdefault(material, {})
                data_by_material[material][record['alias']] = record
            except KeyError:
                # error still exists, e.g. using material rather than Material, which needs to be caught
                # however the reporting should have already been done by validation
                pass

        for record in self.data:
            # if the record is with status Error, no more validation will be done
            if self.validation_results[record['alias']].get_overall_status() == VRConstants.ERROR:
                continue
            record_result = self.validation_results[record['alias']]
            record_id = record['attributes'][self.id_field][0]['value']
            # check relationship
            relationships = record.get('sampleRelationships', [])
            related: List[Dict] = []
            for relationship in relationships:
                if 'accession' in relationship:
                    # target is biosample accession which is checked in validation.check_usi_structure
                    target = relationship['accession']
                    url = f"https://www.ebi.ac.uk/biosamples/samples/{target}"
                    response = requests.get(url)
                    status = response.status_code
                    if status != 200:
                        record_result.add_validation_result_column(
                            VRC(VRConstants.WARNING, f"Fail to retrieve record {target} from "
                                f"BioSamples as required in the relationship", record_id, 'sampleRelationships'
                                , VRConstants.GENERAL))
                    else:
                        # at the moment, no any IMAGE data in BioSamples
                        # check project = IMAGE
                        # parse into memory
                        pass
                else:
                    # in the current ruleset, derived from only from organism to specimen,
                    # so safe to only check organism
                    target: str = relationship['alias']
                    if target in data_by_material['organism']:
                        related.append(dict(data_by_material['organism'][target]))
                    else:
                        record_result.add_validation_result_column(
                            VRC(VRConstants.ERROR, f"Could not locate the referenced record {target}",
                                record_id, 'sampleRelationships', VRConstants.RELATIONSHIP))
                self.validation_results[record['alias']] = record_result

            # if error found during relationship checking, skip context validation
            # because some context validation (relationship check etc) could not be carried out
            if self.validation_results[record['alias']].get_overall_status() == VRConstants.ERROR:
                continue

            record_result = validation.context_validation(record, record_result, related)

            if record_result.is_empty():
                record_result.add_validation_result_column(VRC("Pass", "", record_result.record_id, "",
                                                               VRConstants.EMPTY))
            self.validation_results[record['alias']] = record_result

    def get_validation_results(self) -> List[VRR]:
        """
        Get the validation results
        :return: the list of ruleset-based and context validation results
        """
        return list(self.validation_results.values())

    def is_data_ready(self) -> bool:
        """
        Check whether data has been successfully loaded
        :return: True when data is ready
        """
        return self.data_ready_flag

    def is_ruleset_ready(self) -> bool:
        """
        Check whether ruleset has been successfully loaded
        :return: True when ruleset is ready
        """
        return self.ruleset_pass_flag

    def get_title(self) -> str:
        """
        Get the title of submission
        :return: submission title
        """
        return self.title
