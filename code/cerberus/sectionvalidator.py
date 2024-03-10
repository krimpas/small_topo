import logging
import appvalidator
from dotenv import load_dotenv
from nornir.core.task import Task, Result
from nornir_utils.plugins.tasks.data import load_yaml
from prettytable import PrettyTable


# This is a mapping of section names to cerberus validators,
# Each section corresponds to the cerberus-like validator.

section_to_validator_map = {
    "interfaces": appvalidator.L3ifacevalidator,
    "ospf": appvalidator.Ospfvalidator,
    "keychains": appvalidator.Keychainsvalidator,
}

# Load the environment variables.
load_dotenv()


class SectionValidator:
    """
    Class for loading YAML data and schema and performing validation.

    Loads the yaml files which are keeping in specific directories.
    For data yaml files the directory ${YML_DIR}/{device}
    For schema yaml files is the directory ${SCHEMA_DIR}/{device}
    The class validates the yaml data against the relevanr schema yaml.

    Attributes
    ----------
    data_dir : str
        Keeps the directory keeping the configuration data yaml files.
    schema_dir : str
        Keeps the directory keeping the schema yaml files.
    section : str
        The configuration section (i.e L3interfaces, ospf , ACLs etc)
    data : dict
        The configuration data dict.
    schema : dict
        The schema data dict.

    Methods
    -------
    load_data_and_schema(task)
        Loads the data and schema data into dictionaries using Nornir tasks.

    validate_data_against_schema(task)
        Validates the configuraiton data against the schema using Nornir tasks,

    """

    def __init__(self, data_dir: str, schema_dir: str, section: str):
        """
        Initializes the SectionValidator object.

        Parameters
        ----------
        data_dir : str
            The directory path for YAML data files.
        schema_dir : str:
            The directory path for YAML schema files.
        section :str
            The configuration section.(interfaces, ospf etc)

        """
        self.data_dir = data_dir
        self.schema_dir = schema_dir
        self.section = section
        self.data = None
        self.schema = None

    def load_data_and_schema(self, task: Task) -> Result:
        """
        Loads YAML data and schema from files using the Nornir load_yaml plugin.

        Build the full pathnames for the configuration and schema YAML files
        and use them to fetch YAML data. The YAML contents are fetched using
        Nornir plugin load_yaml.

        Parameters
        ----------
        task : Task
            The Nornir task used to run the loading of YAML files

        Returns
        -------
        Result : Object dict-like
            Returns 2 dictionaries attached to the Result object. The 1st is
            ['data'] and contains the configuration data dictionary and 2nd
            ['schema'] contains the schema dictionary.

        """
        # Build full pathname for data YAML file
        data_file = f"{self.data_dir}/{task.host}/{task.host}_{self.section}.yml"
        # Build full pathname for the schema YANL file.
        schema_file = f"{self.schema_dir}/{self.section}_schema.yml"

        data_result = task.run(
            name=f"Loading data from {data_file}",
            task=load_yaml,
            file=data_file,
            severity_level=logging.DEBUG,
        )

        schema_result = task.run(
            name=f"Loading schema from {schema_file}",
            task=load_yaml,
            file=schema_file,
            severity_level=logging.DEBUG,
        )

        return Result(
            host=task.host,
            result={"data": data_result.result, "schema": schema_result.result},
        )

    def validate_data_against_schema(self, task: Task) -> Result:
        """
        Performs validation of data against the loaded schema.

        The data and schema are loaded into the class members dictionaries.
        The validation is performed by using Cerberus-like classes.

        Parameters
        ----------
        task :Task
            The Nornir task performing the schema validation process.

        Returns
        -------
        Result : Object dict-like
            Returns 2 variables attached to the Result object. The 1st is
            ['is_valid'] which is True if validation succeded, else False
            and the 2nd ['validation_errors'] is dictionary containing the
            errors occured, if any.
        """

        data_schema_result = self.load_data_and_schema(task)
        # save the data
        self.data = data_schema_result.result["data"]
        self.schema = data_schema_result.result["schema"]
        # Perform the actual validation
        v = section_to_validator_map[self.section](self.schema)
        retcode = v.validate(self.data)

        return Result(
            host=task.host, result=dict(is_valid=retcode, validation_errors=v.errors)
        )
