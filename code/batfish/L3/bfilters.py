"""
Name:
-----
    bfilters.py

Description:
------------
    Consists of 2 Batfish related classes used for the offline Validation\n
    checks of Layer 3 interfaces.

Classes:
--------
    BatFilter

Misc variables:
---------------
    __all__
    __version__
    __author__
"""

__all__ = ["BatFilter"]
__version__ = "0.0.1"
__author__ = "Krimpas George"


from ipaddress import IPv4Interface, ip_network
from .nodel3 import NodeL3


class BatFilter:
    """
    Provides predicates used to filter BatFish DataFrames.
    """

    def __init__(self):
        pass

    @staticmethod
    def interface_vrf(row, vrf: str = "default") -> bool:
        """
        Checks if an interface VRF matches the input VRF
        """
        return row.VRF == vrf

    @staticmethod
    def interface_mtu(row, mtu=1500) -> bool:
        """
        Compares the interface MTU configured against the MTU argument.
        """
        return row.MTU == mtu

    @staticmethod
    def interface_up(row) -> bool:
        """
        Checks if an interface is Admin_Up.
        """
        return row.Admin_Up

    @staticmethod
    def interface_active(row) -> bool:
        """
        Checks if an interface is Active.
        """
        return row.row.Active

    @staticmethod
    def interface_prefix(row, ipv4prefix: str) -> bool:
        """
        Checks against input ipv4/prefix length.
        """
        return row.Primary_Address == ipv4prefix

    @staticmethod
    def interface_one_prefix(row) -> bool:
        """
        Checks if only one ipv4/prefix per interface.
        """
        return len(row.All_Prefixes) <= 1
