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
from pybatfish.datamodel.primitives import Interface

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

    device = TopoSection(
        bf=bf,
        sot=ifaces[task.host.name],
        node=f"{task.host.name}",
        properties="Declared_Names",
    )

    topo, data, statistics = device.call_method_by_name(func_name, **kwargs)

    return Result(
        host=task.host, result=dict(topo=topo, data=data, statistics=statistics)
    )


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
        self,
        bf: Session,
        sot: List,
        node: str = None,
        properties: str = "Declared_Names",
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
        tmp_actual = (
            self.session_bf.q.interfaceProperties(nodes=node, properties=properties)
            .answer()
            .frame()
        )
        self.actual = tmp_actual[
            tmp_actual.apply(
                lambda row: row["Interface"].hostname == node
                and not row["Interface"].interface.startswith("Loop"),
                axis=1,
            )
        ]

        self.layer3_topo = self.session_bf.q.layer3Edges(nodes=node).answer().frame()
        #
        self.actual_not_in_topo = self._build_erroneous_topo2(
            left_df=self.actual, right_df=self.layer3_topo
        )

        tmp_layer3_sot = self._build_sot(source_of_truth=sot)

        self.layer3_sot = tmp_layer3_sot[
            tmp_layer3_sot.apply(
                lambda row: not row["Interface"].interface.startswith("Loop"),
                axis=1,
            )
        ]

        self.sot_not_in_topo = self._build_erroneous_topo2(
            left_df=self.layer3_sot, right_df=self.layer3_topo
        )

        self.topo_not_in_sot = self._build_erroneous_topo2(
            left_df=self.layer3_topo, right_df=self.layer3_sot
        )

    def _build_sot(self, source_of_truth: List = None) -> pd.DataFrame:
        """
        Creates the SoT Dataframe for the L3 Interfaces.

        Parameters
        ----------
        source_of_truth: List
            The source of truth for L3 Interfaces.

        Returns
        -------
        Dataframe
        The SoT Dataframe for the L3 Interfaces.
        """
        sot_list = []
        for sot_item in source_of_truth:
            new_item = Interface(hostname=self.node, interface=sot_item)
            sot_list.append(new_item)
        return pd.DataFrame.from_dict({"Interface": sot_list})

    def _build_erroneous_topo2(self, left_df: pd.DataFrame, right_df: pd.DataFrame):
        """
        Used to create the Unexpected L3 Interfaces and Missing L3\n
        Interfaces DataFrame. This is achieved by merging the left_df\n
        and right_df DataFrames on "Interfaces" column by performing\n
        LEFT ANTI JOIN.

        Parameters
        ----------
        left_df: pd.DataFrame
            The left dataframe for the LEFT join.
        right_df: pd.DataFrame
            The right dataframe for the LEFT join.

        Returns
        -------
        erroneous_ifaces: Dataframe
            If the left DataFrame is sot and the right one is actual\n
            then returns the Missing L3 Interfaces. If vice versa\n
            returns the Unexpected L3 Interfaces.

        """
        #
        outer = pd.merge(
            left_df[["Interface"]],
            right_df[["Interface"]],
            how="outer",
            left_on="Interface",
            right_on="Interface",
            indicator=True,
        )

        anti_join = (
            outer[(outer["_merge"] == "left_only")]
            .drop(columns=["_merge"])
            .reset_index(drop=True)
        )

        return anti_join

    def layer3_topo_erroneous(self):
        """
        DataFrame contains the erroneous elements. This is done
        by merging the following DataFrames:
        1. The Source of Truth elements.
        2. The actual configured elements.
        3. The unexpected configured elements.
        4. the missing elements.

        Returns
        -------
        tmp_erroneous: DataFrame
            The DataFrame containing all the above DataFrames.`
        """

        tmp_actual = self.actual_not_in_topo
        tmp_actual.rename(
            mapper={"Interface": "Actual_Not_in_L3_Topo"}, axis=1, inplace=True
        )

        tmp_unexpected = self.topo_not_in_sot
        tmp_unexpected.rename(
            mapper={"Interface": "L3_Topo_Not_in_SoT"}, axis=1, inplace=True
        )

        tmp_missing = self.sot_not_in_topo
        tmp_missing.rename(
            mapper={"Interface": "SoT_Not_in_L3_Topo"}, axis=1, inplace=True
        )

        tmp_erroneous = pd.concat(
            [tmp_actual, tmp_unexpected, tmp_missing], axis=1
        ).reset_index(drop=True)

        tmp_erroneous.fillna("-", inplace=True)
        # tmp_erroneous.index.name = "#"

        return tmp_erroneous

    def layer3_topo_statistics(self):
        """
        Calculates the status and statistical info of the checks. The
        status of the check is PASSED if the missing and unexpected
        DataFrames are empty, otherwise the status is FAILED.

        Returns
        -------
        stats: DataFrame
            The statistical DataFrame of the check.
        """
        is_actual_not_in_topo = self.actual_not_in_topo.shape[0] == 0
        is_sot_not_in_topo = self.sot_not_in_topo.shape[0] == 0
        is_topo_not_in__sot = self.topo_not_in_sot.shape[0] == 0

        error_code, status = (
            (0, "PASSED")
            if is_actual_not_in_topo and is_sot_not_in_topo and is_topo_not_in__sot
            else (-1, "FAILED")
        )

        stats = {
            "retcode": [error_code],
            "ActualNotInTopo": [self.actual_not_in_topo.shape[0]],
            "SoTNotInTopo": [self.sot_not_in_topo.shape[0]],
            "TopoNotInSoT": [self.topo_not_in_sot.shape[0]],
            "Status": [status],
        }
        return pd.DataFrame.from_dict(stats)

    def get_topo(self):
        """returns topo layer3 interfaces"""
        return (
            self.layer3_topo,
            self.layer3_topo_erroneous(),
            self.layer3_topo_statistics(),
        )

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
    for h, res in topo_result.items():
        print_title(f"Host=[{h}]=>L3 Topology")
        print(res.result["topo"])
        print_title(f"Host=[{h}]=>L3 Topo Errors")
        print(res.result["data"])
        print_title(f"Host=[{h}]=>L3 Topo statistics")
        print(res.result["statistics"])
        print(80 * "+")

    print_title("Total Summary Statistics for all Hosts")
    tmp_df = process_stats(topo_result)

    tmp_pt = dataframe_to_prettytable(tmp_df, title="Summary Statistics")
    print(tmp_pt)
    print_title("END: Total Summary Statistics for all Hosts")
    print(80 * "+")
    print(80 * "+")
    print_result(topo_result)
    print(80 * "+")


if __name__ == "__main__":
    main()
