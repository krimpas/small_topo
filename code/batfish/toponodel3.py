"""
Name:
-----
    toponodel3.py\n

Description:
------------
    Consists of Batfish related classes used for the offline Validation\n
    checks of Layer 3 interfaces.

Classes:
--------
    TopoNodeL3\n

Misc variables:
---------------
    __all__\n
    __version__\n
    __author__\n
"""

__all__ = ["L3TopoNode"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import Dict
import pandas as pd
from pybatfish.client.session import Session


class L3TopoNode:
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

    layer3_topo: Batfish Dataframe
        Keeps the dataframe L3 topology elements of the specified node as
        a result of bf.q.layer3Edges batfish question.

    Methods
    -------

    """

    def __init__(self, bf: Session, node: str = "") -> None:
        """
        Initializes the layer3_ifaces Dataframe with the interface info as a
        result of the bf.q.nodeProperties batfish question for the
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

        self.layer3_topo = self.session_bf.q.layer3Edges(nodes=node).answer().frame()

        self.layer3_configured = (
            self.session_bf.q.nodeProperties(nodes=node, properties="Interfaces")
            .answer()
            .frame()
        )

        self.layer3_unexpected = None
        self.layer3_missing = None

    def unexpected(self, nodedict: Dict = None):
        """
        Calculates the unexpected interfaces found in the actual
        configuration.

        Returns:
            Dataframe: contains unexpected interfaces found in the
            configuration
        """
        # fetch the list of configured interfaces
        configured = self.layer3_configured.iloc[0]["Interfaces"]
        # create a list of interfaces based on actual configuration
        actual_interfaces = pd.DataFrame({"Interfaces": configured})
        # create a dataframe of interfaces based on SoT
        sot_interfaces = pd.DataFrame({"Interfaces": nodedict[self.node]})
        # Calculate the Unexpected configured interfaces
        unexpected_ifaces = pd.merge(
            actual_interfaces,
            sot_interfaces[["Interfaces"]],
            on="Interfaces",
            how="left",
            indicator=True,
        )

        unexpected_ifaces = (
            unexpected_ifaces[unexpected_ifaces["_merge"] == "left_only"]
            .drop(columns=["_merge"])
            .reset_index(drop=True)
        )

        self.layer3_unexpected = unexpected_ifaces

        print(unexpected_ifaces)
        return unexpected_ifaces

    def missing(self, ifacelist: Dict):
        """
        Calculates the missing interfaces defined in the SoT but not
        in the actual configuration.

        Returns:
            Dataframe: contains interfaces of source of truth,
            missing
        """
        # fetch the list of configured interfaces
        configured = self.layer3_configured.iloc[0, 0]
        # create a list of interfaces based on actual configuration
        actual_interfaces = pd.DataFrame({"Interfaces": configured})
        # create a dataframe of interfaces based on SoT
        sot_interfaces = pd.DataFrame({"Interfaces": ifacelist[self.node]})
        # Calculate the Unexpected configured interfaces
        missing_ifaces = actual_interfaces[
            sot_interfaces.Interfaces.isin(actual_interfaces.Interfaces) == False
        ]

        self.layer3_missing = missing_ifaces
        return missing_ifaces

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

    def myprint(self):

        return self.layer3_configured._get_value(0, "Interfaces")
