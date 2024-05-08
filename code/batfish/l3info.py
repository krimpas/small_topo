"""
Name:
-----
    l3ifaces.py\n

Description:
------------
    Consists of 2 Batfish related classes used for the offline Validation\n
    checks of Layer 3 interfaces.

Classes:
--------
    NodeL3InterfaceInfo\n
    TopoL3InterfaceInfo\n

Misc variables:
---------------
    __all__\n
    __version__\n
    __author__\n
"""

__all__ = ["NodeL3InterfaceInfo"]
__version__ = "0.0.1"
__author__ = "Krimpas George"


from ipaddress import IPv4Interface, ip_network, ip_interface
from bfish_L3iface_props import L3IFACE_TYPES
from pybatfish.client.session import Session
import pandas as pd
import numpy as np

ifaces = {
    "r1": ["GigabitEthernet2", "GigabitEthernet4", "Loopback0"],
    "r2": ["GigabitEthernet2", "GigabitEthernet3", "GigabitEthernet4", "Loopback0"],
    "r3": ["GigabitEthernet2", "GigabitEthernet3", "Loopback0"],
    "r4": ["GigabitEthernet0/1", "Loopback0"],
    "r5": ["GigabitEthernet0/1", "GigabitEthernet0/2", "Loopback0", "Loopback5"],
}


class NodeL3InterfaceInfo:
    """
    Keeps the information of all L3 interfaces of a given network node. \n

    Performs the bf.q.interfaceProperties question to the batfish service \n
    in order to fetch configuration info for all interfaces for the node \n
    specified. This Class will be used by Nornir Task to receive the node \n
    as an argument (task.host.name). \n

    Attributes
    ----------
    bf: Session
        An already open batfish Session object used to query the batfish
        service.

    layer3_ifaces: Batfish Dataframe
        Keeps the results (dataframe) of the interfaceProperties batfish
        question for a given topology node.

    duplicates: Batfish Dataframe
        keeps the dataframe of duplicate IPv4 addresses in the specified
        node, if any.

    layer3_topo: Batfish Dataframe
        Keeps the dataframe L3 topology elements of the specified node as
        a result of bf.q.layer3Edges batfish question.

    Methods
    -------
    layer3_check_topo_ifaces(self)
        Checks if L3 Topo and node interfaces match each other.

    layer3_ifacetype(row, ifacetype) -> bool
        Checks if in the interface is physical (i.e 'Gig') or Loopback.

    layer3_iface_Active_Up(row) -> bool
        Checks if the interface is Active and Up.

    layer3_subnet_of(row, asupernet) -> bool
        Checks if the IPv4 address is subnet of the given network.

    layer3_iface_MTU(row, mtu) -> bool
        Checks if the interface's MTU matches the given mtu.

    layer3_fetch_duplicates(self)-> DataFrame
        Calculates the duplicates IPv4 address configured on the node

    only_one_prefix_per_layer3_interface(row) -> bool
        Checks if only one IPv4 is configured on interface.

    is_public_IPv4(row) -> bool
        Checks if interface's IPv4 is a public IPv4.

    layer3_one_public_IPv4(self) -> bool
        Checks if there is only one Public IPv4 address among all
        interfaces of thr node.

    check_layer3_interface(self, anet, ifacetype) -> DataFrame
        Performs a sequence of validation checks common on all
        interfaces of the node.

    """

    def __init__(
        self, bf: Session, node: str = "", properties: str = "", interfaces: str = ""
    ) -> None:
        """
        Initializes the layer3_ifaces Dataframe with the interface info as a
        result of the bf.q.interfaceProperties batfish question for the
        given node.

        Queries by using the nornir (task.host.name) as node parameter.
        The layer3_ifaces dataframe keeps the interface info of the specified
        node.

        Parameters
        ----------
        bf: Session
            The already opened batfish Session object used to query the
            batfish service.
        node: str
            The  Node or router name used by Nornir (task.host.name)
        ifacetype: str
            The Type of Interface ('Loop', 'Gig', 'TenGig', 'Loopback')
        properties: str
            The dataframe columns contained in the results

        Returns
        -------
        None
        """
        self.session_bf = bf
        #
        self.node = node

        self.layer3_ifaces = (
            self.session_bf.q.interfaceProperties(
                nodes=node, interfaces=interfaces, properties=properties
            )
            .answer()
            .frame()
        )
        #
        self.duplicates = self.layer3_ifaces[
            self.layer3_ifaces.duplicated(
                ["Primary_Address", "Primary_Network"], keep=False
            )
        ]
        self.layer3_topo = self.session_bf.q.layer3Edges(nodes=node).answer().frame()

        self.all_configured = (
            self.session_bf.q.nodeProperties(nodes=node, properties="Interfaces")
            .answer()
            .frame()
        )

    def missing_and_unexpected(self):
        """
        Calculates the missing and unexpected interfaces found

        Returns:
            Dataframe: contains interfaces of source of truth,
            missing and unexpected
        """
        reference_set = ifaces[self.node]

        unexpected_interfaces = self.all_configured["Interfaces"].map(
            lambda x: set(x) - set(reference_set)
        )

        missing_set = self.all_configured["Interfaces"].map(
            lambda x: set(reference_set) - set(x)
        )

        diff_df = pd.DataFrame(
            {
                pd.Series(self.all_configured["Interfaces"]),
                pd.Series(unexpected_interfaces),
                pd.Series(missing_set),
            },
        )

        indicator = "NA"
        diff_df.fillna(indicator, inplace=True)

        return diff_df

    def layer3_check_topo_ifaces(self) -> bool:
        """
        Checks if the number and names of node physical interfaces matches
        the number and names of interfaces belonging in the L3 topology.

        Returns
        -------
        Batfish Dataframe
            layer3_topo or joined_frame
        """
        if self.layer3_ifaces.shape[0] != self.layer3_topo.shape[0]:
            return self.layer3_topo

        joined_frame = pd.merge(
            self.layer3_topo, self.layer3_ifaces, on="Interface", how="inner"
        )

        if joined_frame.shape[0] != self.layer3_topo.shape[0]:
            return self.layer3_ifaces

        return joined_frame

    @staticmethod
    def layer3_ifacetype(row, ifacetype=L3IFACE_TYPES.LOOP.value) -> bool:
        """
        Checks if the interface type starts with the argument ifacetype.

        Parameters
        ----------
        row: Dataframe row
            Represents an interface of the specific node.

        ifacetype: str
            Indicates if the interface is Loopback or Physical.

        Returns
        -------
        bool
            True if a match otherwise False.
        """
        return row.Interface.interface.startswith(ifacetype)

    @staticmethod
    def layer3_interface(row, interface_name: str = "GigabitEthernet2") -> bool:
        """
        Fetches if an interface with name interface_name exists in the
        dataframe.

        Parameters
        ----------
        row: Dataframe row
            Represents an interface of the specific node.

        interface_name: str
            The name of the interface (i.e GigabitEthernet2)

        Returns
        -------
        bool
            True if the interface exists, otherwise False.
        """
        return row.Interface.interface == interface_name

    @staticmethod
    def layer3_iface_active_up(row) -> bool:
        """
        Checks if an interface is both Admin_Up and Active.

        Parameters
        ----------
        row: Dataframe row
            Represents an interface of the specific node.

        Returns
        -------
        bool
            True if a match otherwise False.

        """
        return row.Active and row.Admin_Up

    @staticmethod
    def layer3_iface_vrf(row, vrf: str = "default") -> bool:
        """
        Checks if an interface VRF.

        Parameters
        ----------
        row: Dataframe row
            Represents an interface of the specific node.

        Returns
        -------
        bool
            True if a VRF match otherwise False.

        """
        return row.VRF == vrf

    @staticmethod
    def layer3_subnet_of(row, asupernet="172.16.0.0/24") -> bool:
        """
        Checks if the supernet is a supernet of the interface IPv4 network.

        Parameters
        ----------
        row: Dataframe row
            Represents an interface of the specific node.

        asupernet: str
            Indicates the network prefix.

        Returns
        -------
        bool
            True if the IPv4 of the interface is subnet of the asupernet,
            otherwise False.

        """
        return ip_network(asupernet).supernet_of(ip_network(row.Primary_Network))

    @staticmethod
    def layer3_iface_mtu(row, mtu=1500) -> bool:
        """
        Compares the interface MTU configured against the MTU argument.

        Parameters
        ----------
        row: Dataframe row
            Represents an interface of the specific node.

        mtu: integer
            Indicates the MTU size.

        Returns
        -------
        bool
            True if configured MTU matches mtu argument, otherwise False.
        """
        return row.MTU == mtu

    @property
    def layer3_fetch_duplicates(self):
        """
        Calculates the duplicates IPv4 address configured on the node

        Returns
        -------
            Dataframe : Contains all duplicates or empty.
        """
        return self.layer3_ifaces[
            self.layer3_ifaces.duplicated(
                ["Primary_Address", "Primary_Network"], keep=False
            )
        ]

    @staticmethod
    def only_one_prefix_per_layer3_interface(row) -> bool:
        """
        Checks that only one IPv4 prefix configured i.e (All_Prefixes
        list must be of length 1)

        Parameters
        ----------
        row: Dataframe row
            Represents an interface of the specific node.

        Returns
        -------
        bool
            True if only 1 IPv4 prefix configured, otherwise False.
        """
        return len(row.All_Prefixes) <= 1

    @staticmethod
    def is_public_ipv4(row) -> bool:
        """
        Checks if interface IPv4 address configured is public.

        Parameters
        ----------
        row: Dataframe row
            Represents an interface of the specific node.

        Returns
        -------
        bool
            True if IPv4 prefix configured is public, else False.
        """

        return IPv4Interface(row.Primary_Address).ip.is_global

    @property
    def layer3_one_public_ipv4(self) -> bool:
        """
        Checks if between all configured IPv4 addresses in the node,
        there is only one IPv4 address which is Public or Global.

        Returns
        -------
        retcode: bool
            True if only one public IPv4 prefix is configured in the node,
            else False.

        one_public: Batfish Dataframe
            The dataframe of the Public IPv4 address if any, or empty.
        """
        one_public = self.layer3_ifaces[
            self.layer3_ifaces.apply(
                self.is_public_ipv4,
                axis=1,
            )
        ]
        retcode = one_public.count().Interface == 1
        return retcode, one_public

    def check_layer3_interface(
        self, anet="172.16.0.0/16", ifacetype=L3IFACE_TYPES.LOOP.value
    ):
        """
        Summarizes all Design Conditions required

        Checks if:
        1. the interface type starts with the argument ifacetype
        2. the supernet is a supernet of the interface IPv4 network.
        3. the interface is both Admin_Up and Active.

        Parameters
        ----------
        anet (str, optional)
            Represents the supernet of the interface IPv4 address.
            Defaults to '172.16.0.0/16'.
        ifacetype (str, optional)
            Represents the interface type as: (Loopback, Gigabit).
            Defaults to 'Loop'.

        Returns
        -------
        layer3_ifaces: Batfish DataFrame
            Returns the dataframe of all interfaces satisfying the
            ifacetype criterion but not all others
        """

        return self.layer3_ifaces[
            self.layer3_ifaces.apply(
                lambda row: self.layer3_ifacetype(row, ifacetype=ifacetype)
                and not (
                    self.layer3_subnet_of(row, asupernet=anet)
                    and self.layer3_iface_active_up(row)
                )
                and self.only_one_prefix_per_layer3_interface(row),
                axis=1,
            )
        ]

    def lookup_layer3_interface(self, interface_name: str = "GigabitEthernet2"):
        """
        Lookup a specific interface by using its name

        Parameters
        ----------
        interface_name (str, optional)
            Represents the name of the interface
        Returns
        -------
        layer3_ifaces: Batfish DataFrame
            Returns the dataframe of the interface specified,
        """

        return self.layer3_ifaces[
            self.layer3_ifaces.apply(
                lambda row: self.layer3_interface(row, interface_name=interface_name),
                axis=1,
            )
        ]

    def all_layer3_interfaces(self):
        return self.layer3_ifaces

    def all_node_configured_interfaces(self):
        return self.all_configured

    def call_method_by_name(self, name, **kwargs):
        """
        Performs dynamic calls to any class method by using the
        method name and any arguments needed.

        Parameters
        ----------
        name: (str, mandatory)
            The method name as string
        kwargs: (dict, optional)
            The method parameters values dict if any.

        Returns
        -------
        res (Dataframe)
        """
        res = None
        method = getattr(self, name, None)
        if method:
            res = method(**kwargs)
        return res
