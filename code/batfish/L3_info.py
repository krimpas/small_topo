from ipaddress import ip_network as ipnet
from ipaddress import IPv4Interface
from bfish_L3iface_props import BFISH_L3IFACE_PROPS, L3IFACE_TYPES
from bfish_init import bfish_init


class L3InterfaceInfo:
    def __init__(
        self, node: str = "", properties: str = "", interfaces: str = ""
    ) -> None:
        """
        Initialzes the L3ifaces Dataframe with the results of the
        bfq.InterfaceProperties.

        Args:
            ifacetype: The Type of Interface ('Loop', 'Giga', 'TenGig')
            properties: The dataframe columns contained in the results

        Returns: None
        """
        self.session_bf = bfish_init()
        self.L3ifaces = (
            self.session_bf.q.interfaceProperties(
                nodes=node, interfaces=interfaces, properties=properties
            )
            .answer()
            .frame()
        )

    @staticmethod
    def L3_ifacetype(row, ifacetype=L3IFACE_TYPES.LOOP.value) -> bool:
        """
        Checks if the interface type starts with the argument ifacetype
        """
        return row.Interface.interface.startswith(ifacetype)

    @staticmethod
    def L3_iface_Active_Up(row) -> bool:
        """
        Checks if an interface is both Admin_Up and Active.
        """
        return row.Active and row.Admin_Up

    @staticmethod
    def L3_subnet_of(row, asupernet="172.16.0.0/16") -> bool:
        """
        Checks if the supernet is a supernet of the interface IPv4 network.
        """
        return ipnet(asupernet).supernet_of(ipnet(row.Primary_Network))

    @staticmethod
    def L3_iface_MTU(row, mtu=1500) -> bool:
        """
        Compares the interface MTU configured against the MTU argument.
        """
        return row.MTU == mtu

    @staticmethod
    def only_one_prefix_per_L3interface(row) -> bool:
        """
        The All_Prefixes list must be of length 1
        """
        return len(row.All_Prefixes) <= 1

    @staticmethod
    def is_public_IPv4(row) -> bool:
        """
        Checks if the interface configured IPv4 address is public or not.
        """
        return IPv4Interface(row.Primary_Address).ip.is_global

    @property
    def L3_one_public_IPv4(self) -> bool:
        """
        Checks if between configured IPv4 address, there is only one IPv4
        address which is Public or Global
        """
        one_public = self.L3ifaces[
            self.L3ifaces.apply(
                lambda row: self.is_public_IPv4(row),
                axis=1,
            )
        ]
        retcode = True if one_public.count().Interface == 1 else False
        return retcode, one_public

    def check_L3_interface(
        self, anet="172.16.0.0/16", ifacetype=L3IFACE_TYPES.LOOP.value
    ):
        """
        Summarizes all Design Conditions required
        Checks if:
        1. the interface type starts with the argument ifacetype
        2. the supernet is a supernet of the interface IPv4 network.
        3. the interface is both Admin_Up and Active.

        Args:
            anet (str, optional): Represents the supernet of the interface
            IPv4 address. Defaults to '172.16.0.0/16'.
            ifacetype (str, optional): Represents the interface type as:
            (Loopback, Gigabit) Defaults to 'Loop'.

        Returns:
            DataFrame: Returns the dataframe containg all interfaces satisfying
            the ifacetype crierion but not all others
        """

        return self.L3ifaces[
            self.L3ifaces.apply(
                lambda row: self.L3_ifacetype(row, ifacetype=ifacetype)
                and not (
                    self.L3_subnet_of(row, asupernet=anet)
                    and self.L3_iface_Active_Up(row)
                )
                and self.only_one_prefix_per_L3interface(row),
                axis=1,
            )
        ]
