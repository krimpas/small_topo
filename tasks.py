from invoke import task
import os
from dotenv import load_dotenv

load_dotenv()


@task
def lint_yaml(c, directory=f"{os.environ.get('YML_DIR')}/r*/", file_pattern="*.yml"):
    """
    Run yamllint on YAML files in a directory using wildcards.
    """
    c.run(f"yamllint {directory}/{file_pattern}")

@task
def black(c, directory="."):
    """
    Run yamllint on YAML files in a directory using wildcards.
    """
    c.run(f"black {directory} --check --color")

@task
def check(c, section='interfaces'):
    c.run(f"python3 code/cerberus/checkconfig.py --section {section}")