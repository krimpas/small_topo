CERBERUS_DIR := code/cerberus
BATFISH_DIR := code/batfish
YML_DIR := data/yml
SCHEMA_DIR := data/schema/include.d

activate:
	source venv/bin/activate

black:
	@echo "+----------------------------+"
	@echo "| Black Cerberus Python Code |"
	@echo "+----------------------------+"
	black ${CERBERUS_DIR} --check
	@echo "+----------------------------+"
	@echo "| Black Batfish Python Code  |"
	@echo "+----------------------------+"
	black ${BATFISH_DIR} --check

lint:
	@echo "+------------------------------+"
	@echo "| Linting YAML CONF data files |"
	@echo "+------------------------------+"
	yamllint --list-files --format github --strict ${YML_DIR}/r*/
	@echo "+----------------------------+"
	@echo "| Linting YAML SCHEMA files  |"
	@echo "+----------------------------+"
	yamllint --list-files --format github --strict ${SCHEMA_DIR}

config:
	@echo "+----------------------------+"
	@echo "| Cerberus L3 interfaces     |"
	@echo "+----------------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section interfaces
	@echo "+-------------------+"
	@echo "| Cerberus OSPF     |"
	@echo "+-------------------+"
	python3 ${CERBERUS_DIR}/checkconfig.py --section ospf
	@echo "+----------------------------+"
	@echo "| Cerberus OSPF Keychains    |"
	@echo "+----------------------------+"
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
	@echo "+----------------------+"
	@echo "| END OF BATFISH  !!!! |"
	@echo "+----------------------+"