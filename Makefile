CERBERUS_DIR := code/cerberus
BATFISH_DIR := code/batfish
YML_DIR := data/yml
SCHEMA_DIR := data/schema/include.d

activate:
	source venv/bin/activate

black:
	@echo "+-------------------------------+"
	@echo "| Checking Cerberus Python Code |"
	@echo "+-------------------------------+"
	black ${CERBERUS_DIR} --check
	@echo "+-------------------------------+"
	@echo "| Checking Batfish Python Code  |"
	@echo "+-------------------------------+"
	black ${BATFISH_DIR} --check

lint: black
	@echo "+------------------------------+"
	@echo "| Linting YAML CONF data files |"
	@echo "+------------------------------+"
	yamllint --list-files --format github --strict ${YML_DIR}/r*/
	@echo "+----------------------------+"
	@echo "| Linting YAML SCHEMA files  |"
	@echo "+----------------------------+"
	yamllint --list-files --format github --strict ${SCHEMA_DIR}

config: lint
	@echo "+------------------------------+"
	@echo "| Validating L3 interfaces     |"
	@echo "+------------------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section interfaces
	@echo "+---------------------+"
	@echo "| Validating OSPF     |"
	@echo "+---------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section ospf
	@echo "+------------------------------+"
	@echo "| Validating OSPF Keychains    |"
	@echo "+------------------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section keychains