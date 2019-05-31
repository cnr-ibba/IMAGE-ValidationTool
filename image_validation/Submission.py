from . import ValidationResult, validation
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

    """
    def __init__(self, title, id_field: str = "Data source ID"):
        self.title = title
        self.validation_results: Dict[str, ValidationResult.ValidationResultRecord] = dict()
        self.data = None
        self.data_ready_flag = False
        self.ruleset = None
        self.ruleset_pass_flag = False
        self.id_field = id_field
        self.general_errors: List[str] = list()

    def load_data(self, data_file: str, section: str = '', id_field: str = 'Data source ID'):
        self.data_ready_flag = False
        self.general_errors = list()
        try:
            with open(data_file) as infile:
                self.data = json.load(infile)
        except FileNotFoundError:
            self.general_errors.append(f"Could not find the file {data_file}")
            return
        except json.decoder.JSONDecodeError:
            self.general_errors.append(f"The provided file {data_file} is not a valid JSON file.")
            return
        if len(section) > 0:
            if section in self.data:
                self.data = self.data[section]
        # check usi structure
        self.general_errors = validation.check_usi_structure(self.data)
        if self.general_errors:
            return
        # check duplicate id
        self.general_errors = validation.check_duplicates(self.data, id_field)
        if self.general_errors:
            return
        logger.info("All sample records have unique data source ids")
        self.data_ready_flag = True

    def load_ruleset(self, ruleset_file: str) -> None:
        self.ruleset_pass_flag = False
        self.general_errors = list()
        try:
            self.ruleset = validation.read_in_ruleset(ruleset_file)
        except KeyError as e:
            self.general_errors.append(str(e))
            return
        self.general_errors = validation.check_ruleset(self.ruleset)
        if self.general_errors:
            return
        logger.info("Ruleset loaded")
        self.ruleset_pass_flag = True

    def validate(self):
        """
        Validate the data against the ruleset
        the data needs to be scanned twice, first time to validate individual record
        second time to validate anything involving with more than one record e.g. relationships and context validation
        :return:
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
            if self.validation_results[record['alias']].get_overall_status() == "Error":
                continue
            record_result = self.validation_results[record['alias']]
            record_id = record['attributes'][self.id_field][0]['value']
            # check relationship
            relationships = record.get('sampleRelationships', [])
            related: List[Dict] = []
            for relationship in relationships:
                target: str = relationship['alias']
                if target.startswith("SAM"):  # BioSamples data
                    url = f"https://www.ebi.ac.uk/biosamples/samples/{target}"
                    response = requests.get(url)
                    status = response.status_code
                    if status != 200:
                        record_result.add_validation_result_column(
                            ValidationResult.ValidationResultColumn(
                                "Warning", f"Fail to retrieve record {target} from "
                                f"BioSamples as required in the relationship", record_id, 'sampleRelationships'))
                    else:
                        # at the moment, no any IMAGE data in BioSamples
                        pass
                else:
                    # in the current ruleset, derived from only from organism to specimen,
                    # so safe to only check organism
                    if target in data_by_material['organism']:
                        related.append(dict(data_by_material['organism'][target]))
                    else:
                        record_result.add_validation_result_column(
                            ValidationResult.ValidationResultColumn(
                                "Error", f"Could not locate the referenced record {target}",
                                record_id, 'sampleRelationships'))
                self.validation_results[record['alias']] = record_result

            # if error found during relationship checking, skip context validation
            # because some context validation (relationship check etc) could not be carried out
            if self.validation_results[record['alias']].get_overall_status() == "Error":
                continue

            record_result = validation.context_validation(record, record_result, related)

            if record_result.is_empty():
                record_result.add_validation_result_column(
                    ValidationResult.ValidationResultColumn("Pass", "", record_result.record_id, ""))
            self.validation_results[record['alias']] = record_result

    def get_validation_results(self) -> List[str]:
        return list(self.validation_results.values())

    def is_data_ready(self) -> bool:
        return self.data_ready_flag

    def is_ruleset_ready(self) -> bool:
        return self.ruleset_pass_flag

    def get_general_errors(self) -> List[str]:
        return self.general_errors

    def get_title(self) -> str:
        return self.title
