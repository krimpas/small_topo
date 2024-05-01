CERBERUS_DIR := code/cerberus
BATFISH_DIR := code/batfish
YML_DIR := data/yml
SCHEMA_DIR := data/schema/include.d
SECTION := ""
PYTHON3 := ./venv/bin/python3.9

all: black lint config clean

.PHONY: clean black lint config batfish

.DEFAULT_GOAL := help

help:
	@echo "make clean"
	@echo "  clean un-neeeded files"
	@echo "make black"
	@echo "  black the python source code"
	@echo "make lint"
	@echo "  lint the YAML files"
	@echo "make config"
	@echo "  check configuration sections"
	@echo "make batfish"
	@echo "  batfish questions for offline checks"

activate:
	source venv/bin/activate

deactivate:
	deactivate

clean:
	@echo "Cleaning Up ..."
	rm -rf ./__pycache__
	rm -rf ${CERBERUS_DIR}/__pycache__
	rm -rf ${BATFISH_DIR}/__pycache__

black: ${CERBERUS_DIR}/*.py 
	@echo "+----------------------------+"
	@echo "| Black Cerberus Python Code |"
	@echo "+----------------------------+"
	$@ $^ --check
	@echo "+----------------------------+"
	@echo "| Black Batfish Python Code  |"
	@echo "+----------------------------+"
	$@ ${BATFISH_DIR} --check

yamllint: ${YML_DIR}/r*
	@echo "+------------------------------+"
	@echo "| Linting YAML CONF data files |"
	@echo "+------------------------------+"
	$@ --list-files --format github --strict $^
	@echo "+----------------------------+"
	@echo "| Linting YAML SCHEMA files  |"
	@echo "+----------------------------+"
	$@ --list-files --format github --strict ${SCHEMA_DIR}

config:
	@echo "+-------------------------------------+"
	@echo "| Cerberus Section: L3 interfaces     |"
	@echo "+-------------------------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section interfaces
	@echo "+----------------------------+"
	@echo "| Cerberus Section: OSPF     |"
	@echo "+----------------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section ospf
	@echo "+-------------------------------------+"
	@echo "| Cerberus Section: OSPF Keychains    |"
	@echo "+-------------------------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section keychains

batfish:
	@echo "+----------------------------------+"
	@echo "| BatFishing Node L3 interfaces    |"
	@echo "+----------------------------------+"
	python3 ${BATFISH_DIR}/L3check.py
	@echo "+----------------------------------+"
	@echo "| BatFishing Overall L3 Topology   |"
	@echo "+----------------------------------+"
	python3 ${BATFISH_DIR}/L3check2.py

lint: yamllint black

conf: lint config

L3: lint
	@echo "+----------------------------------+"
	@echo "| Cerberus SECTION: ${SECTION}     |"
	@echo "+----------------------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section ${SECTION}