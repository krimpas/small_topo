"""
This file contains all functions needed in order to let the
Nornir tasks.
"""

import os
import logging
import pandas as pd
from l3info import NodeL3InterfaceInfo
from bfish_L3iface_props import BFISH_L3IFACE_PROPS
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result, print_title
from dotenv import load_dotenv
from bfish_init import bfish_init
from pybatfish.client.session import Session
from toponodel3 import NodeSession
from customutils import process_stats, dataframe_to_prettytable, echo_nornir_result
from typing import List
from pprint import pprint

ifaces = {
    "r1": ["GigabitEthernet2", "GigabitEthernet4", "Loopback0"],
    "r2": ["GigabitEthernet2", "GigabitEthernet3", "GigabitEthernet4", "Loopback0"],
    "r3": ["GigabitEthernet2", "GigabitEthernet3", "Loopback0"],
    "r4": ["GigabitEthernet0/1", "GigabitEthernet3", "Loopback0"],
    "r5": ["GigabitEthernet0/1", "GigabitEthernet0/2", "Loopback0", "Loopback5"],
}

load_dotenv()


def exec_topo(task: Task, bf: Session, func_name: str = "", **kwargs) -> Result:
    """mplah"""

    device = TopoSection(bf=bf, node=f"{task.host.name}", properties="Interfaces")

    data = device.call_method_by_name(func_name, **kwargs)

    return Result(host=task.host, result=data)


class TopoSection(NodeSession):
    """
    Keeps an individual config section of topology.

    Attributes
    ----------
    configured: Batfish DataFrame
        Keeps the configuration section info of the specified node.\n
        The config section is retrieved using the Batfish question \n
        bf.q.nodeProperties().

    actual: Batfish DataFrame
        Dataframe derived from configured attribute.\n

    """

    def __init__(
        self, bf: Session, node: str = None, properties: str = "Interfaces"
    ) -> None:
        """
        Parameters
        ----------
        bf: Session
            The already opened batfish Session object used to query the
            batfish service.

        node: str
            The  Node or router name used by Nornir (task.host.name).

        properties: str
            The individual config feature of the node (i.e Interfaces)\n
            It is used by the Batfish Query bf.q.nodeProperties()\n

        """
        super().__init__(bf, node)

        # Get the Node configuration info
        self.actual = (
            self.session_bf.q.interfaceProperties(nodes=node, properties=properties)
            .answer()
            .frame()
        )

        self.layer3_topo = self.session_bf.q.layer3Edges(nodes=node).answer().frame()

    def get_topo(self):
        """returns topo layer3 interfaces"""
        return self.layer3_topo

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


def main():
    """This is the main function which executes all the Nornir Tasks."""
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    # Initialize Batfish session
    bf_session = bfish_init()

    topo_result = nr.run(
        name="Erroneous L3 Interface Configuration",
        task=exec_topo,
        bf=bf_session,
        func_name="get_topo",
        severity_level=logging.INFO,
    )
    print_result(topo_result)


if __name__ == "__main__":
    main()
