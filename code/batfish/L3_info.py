from ipaddress import ip_network as ipnet
from ipaddress import IPv4Interface
from bfish_L3iface_props import L3IFACE_TYPES
from pybatfish.client.session import Session


class L3InterfaceInfo:
    """
    Class for keeping the information of all interfaces of a given node.

    Performs the bf.q.interfaceProperties question to the batfish service
    in order to fetch configuration info for all interfaces for the node
    specified. This Class will be used by Nornir Task to receive the node
    as an argument (task.host.name).

    Attributes
    ----------
    bf: Session
        An already open batfish Session object used to query the batfish
        service.

    L3ifaces: Batfish Dataframe
        Keeps the results (dataframe) of the interfaceProperties batfish
        question for a given topology node.

    Methods
    -------
    L3_ifacetype(row, ifacetype) -> bool
        Checks if in the interface is physical (i.e 'Gig') or Loopback.

    L3_iface_Active_Up(row) -> bool
        Checks if the interface is Active and Up.

    L3_subnet_of(row, asupernet) -> bool
        Checks if the IPv4 address is subnet of the given network.

    L3_iface_MTU(row, mtu) -> bool
        Checks if the interface's MTU matches the given mtu.

    only_one_prefix_per_L3interface(row) -> bool
        Checks if only one IPv4 is configured on interface.

    is_public_IPv4(row) -> bool
        Checks if interface's IPv4 is a public IPv4.

    L3_one_public_IPv4(self) -> bool
        Checks if there is only one Public IPv4 address among all
        interfaces of thr node.

    check_L3_interface(self, anet, ifacetype) -> DataFrame
        Performs a sequence of validation checks common on all
        interfaces of the node.

    """

    def __init__(
        self, bf: Session, node: str = "", properties: str = "", interfaces: str = ""
    ) -> None:
        """
        Initializes the L3ifaces Dataframe with the interface info as a
        result of the bf.q.interfaceProperties batfish question for the
        given node.

        Queries by using the nornir (task.host.name) as node parameter.
        The L3ifaces dataframe keeps the interface info of the specified
        node.

        Parameters
        ----------
        bf: Session
            The already open batfish Session object used to query the
            batfish service.
        node: str
            The  Node or router name used by Nornir (task.host.name)
        ifacetype: str
            The Type of Interface ('Loop', 'Gig', 'TenGig')
        properties: str
            The dataframe columns contained in the results

        Returns
        -------
        None
        """
        self.session_bf = bf
        #
        self.L3ifaces = (
            self.session_bf.q.interfaceProperties(
                nodes=node, interfaces=interfaces, properties=properties
            )
            .answer()
            .frame()
        )
        #
        self.duplicates = self.L3ifaces[self.L3ifaces.duplicated("Primary_Address")]

        self.L3topo = self.session_bf.q.layer3Edges(nodes=node).answer().frame()

    @staticmethod
    def L3_ifacetype(row, ifacetype=L3IFACE_TYPES.LOOP.value) -> bool:
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
    def L3_iface_Active_Up(row) -> bool:
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
    def L3_subnet_of(row, asupernet="172.16.0.0/24") -> bool:
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
        return ipnet(asupernet).supernet_of(ipnet(row.Primary_Network))

    @staticmethod
    def L3_iface_MTU(row, mtu=1500) -> bool:
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

    @staticmethod
    def only_one_prefix_per_L3interface(row) -> bool:
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
    def is_public_IPv4(row) -> bool:
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
    def L3_one_public_IPv4(self) -> bool:
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
            L3ifaces: Batfish DataFrame
                Returns the dataframe of all interfaces satisfying the
                ifacetype criterion but not all others
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
