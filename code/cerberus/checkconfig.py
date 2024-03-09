import os
import logging
import argparse
from dotenv import load_dotenv
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result, print_title
from nornir.core.filter import F
from sectionvalidator import SectionValidator
from pprint import pprint

load_dotenv()

def main():

    # Define directories and section
    data_directory = os.environ.get("YML_DIR")
    schema_directory = os.environ.get("SCHEMA_DIR")

    # Prepare the argparse command line arguments.
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-s",
        "--section",
        type=str,
        required=False,
        default="all",
        help=f"Defines the configuration section",
    )

    sargs = parser.parse_args()

    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))

    # Filet inventory using section
    filtered_hosts = nr.filter(F(conf_sections__contains=sargs.section))

    # Initialize SectionValidator
    val = SectionValidator(data_directory, schema_directory, sargs.section)

    # Run the validation task on all filtered hosts
    result = filtered_hosts.run(
        name=f"YAML Valitation Config: {sargs.section}",
        task=val.validate_data_against_schema,
        severity_level=logging.INFO,
    )

    # Print the results
    print_result(result)

    for h in filtered_hosts.inventory.hosts.keys():
        if not result[h].result["retcode"]:
            exit(-123)
    print_title(f">>>|{sargs.section} YAML check: PASSED |<<<")
    return 0


if __name__ == "__main__":
    main()
