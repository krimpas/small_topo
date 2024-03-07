
from cerberus import Validator
from ipaddress import ip_address, ip_interface
from dotenv import load_dotenv
import yaml
import os

# Loads the environment.
load_dotenv()


def load_valid_data(schdir: str = "VALID_DIR"):
    """Loads custom valid data YAML"""
    valid_dir = os.environ.get("VALID_DIR")
    valid_file = f"{valid_dir}/validata.yml"
    with open(valid_file, "r") as f:
        valid_data = yaml.safe_load(f)
    return valid_data


class L3ifacevalidator(Validator):
    """
    Cerberus-like Class that performs validation on L3 interfaces,

    Methods
    -------
    _validate_type_ipv4addr
        Validates if a yaml element is actually an ipv4address

    _validate_type_netmask
        Validates if a yaml element is actually a netmask

    _validate_type_ospf_net_type
        Validates if a yaml element is actualy an enumeration
        of OSPF network type.

    """

    def _validate_type_ipv4addr(self, value):
        """
        Performs a validation if value is a valid ipv4addr.

        Parameters
        ----------
        value : str
            It will be checked if ia a valid ipv4addr.

        Returns
        -------
        bool:
            True if a valid ipv4addr, otherwise False.
        """

        try:
            if ip_address(value):
                return True
        except ValueError:
            return False

    def _validate_type_netmask(self, value):
        """
        Performs a validation if value is a valid netmask.

        Parameters
        ----------
        value : str
            The value that will be checked if ia a valid netmask.

        Returns
        -------
        bool:
            True if a valid netmask, otherwise False.
        """

        try:
            sm = value + "/" + value
            addr = ip_interface(sm)
            if addr.network.network_address:
                return True
        except ValueError:
            return False

    def _validate_type_privipv4addr(self, value):
        """
        Performs a validation if value is a valid Private ipv4addr.
        10.0.0.0/8 172.16.0.0/12 192/168.0.0/16

        Parameters
        ----------
        value : str
            It will be checked if ia a valid Private ipv4addr.

        Returns
        -------
        bool:
            True if a valid Private ipv4addr, otherwise False.
        """

        try:
            if ip_address(value).is_private:
                return True
        except ValueError:
            return False

    def _validate_type_ospf_net_type(self, value):
        """
        Validates if a yaml element is actualy an enumeration
        of OSPF network type.

        Parame
        ters
        ----------
        value : str
            It will be checked if ia a valid OSPF network type.

        Returns
        -------
        bool:
            True if a valid OSPF network type, otherwise False.
        """

        valid = load_valid_data()
        return True if value.lower() in valid["ospf_nets"] else False


class Ospfvalidator(Validator):
    """
    Class For OSPF schema validation using Cerberus-like methods

    Methods
    -------
    _validate_type_ipv4addr
        Validates if a value is a valid ipv4addr.

    """

    def _validate_type_ipv4addr(self, value):
        """
        Performs a validation if value is a valid ipv4addr.

        Parameters
        ----------
        value : str
            It will be checked if ia a valid ipv4addr.

        Returns
        -------
        bool:
            True if a valid ipv4addr, otherwise False.
        """
        try:
            if ip_address(value):
                return True
        except ValueError:
            return False


class Keychainsvalidator(Validator):
    """
    Class For Keychains schema validation.

    Methods
    -------
    _validate_type_crypto_algorithm
        Validates if a value is a valid crypto algorithm.

    """

    def _validate_type_crypto_algorithm(self, value):
        """
        Performs a validation if value is a valid crypto algorithm.

        Parameters
        ----------
        value : str
            It will be checked if ia a valid crypto algorithm.

        Returns
        -------
        bool:
            True if a valid crypto algorithm, otherwise False.
        """

        valid = load_valid_data()
        return True if value.lower() in valid["crypto_algorithms"] else False
