"""
Name:
-----
    nodel3topo.py

Description:
------------
    Consists of Batfish related classes used for the offline Validation
    checks of Layer 3 interfaces.

Classes:
--------
    NodeL3Topo

Misc variables:
---------------
    __all__
    __version__
    __author__
"""

__all__ = ["NodeL3Topo"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import Dict, Optional, Tuple
import pandas as pd
from pybatfish.client.session import Session
from pybatfish.datamodel import Interface
from .nodel3 import NodeL3


class NodeL3Topo(NodeL3):
    """
    Calculates the Layer 3 Topology by querying the Batfish service.

    Attributes
    ----------
    layer3_topo: pd.DataFrame
        DataFrame that keeps the Layer 3 Topology.

    actual_not_in_topo: pd.DataFrame
        Interfaces configured on the node but not in Layer 3 Topology.

    sot_not_in_topo: pd.DataFrame
        Interfaces in SoT but not in Layer 3 Topology.

    topo_not_in_sot: pd.DataFrame
        Interfaces in Layer 3 Topology but not in SoT.
    """

    def __init__(
        self,
        bf: Session,
        sot: Dict,
        node: Optional[str] = None,
        properties: str = "Interface",
    ) -> None:
        super().__init__(bf=bf, sot=sot, node=node, properties=properties)
        self.sot, self.actual = self.filter_loopback()
        self.layer3_topo = self.build_layer3_topo()
        self.actual_not_in_topo = self.left_anti_join(
            left_df=self.actual, right_df=self.layer3_topo
        )
        self.sot_not_in_topo = self.left_anti_join(
            left_df=self.sot, right_df=self.layer3_topo
        )
        self.topo_not_in_sot = self.left_anti_join(
            left_df=self.layer3_topo, right_df=self.sot
        )

    def filter_loopback(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Eliminates Loopback interfaces from self.sot and self.actual DataFrames.

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame]
            DataFrames without Loopback interfaces.
        """

        def is_not_loopback(interface: Interface) -> bool:
            return not interface.interface.startswith("Loop")

        sot_filtered = self.sot[self.sot["Interface"].apply(is_not_loopback)]
        actual_filtered = self.actual[self.actual["Interface"].apply(is_not_loopback)]
        return sot_filtered, actual_filtered

    def build_layer3_topo(self) -> pd.DataFrame:
        """
        Builds the Layer 3 Topology for the node by calling the Batfish question q.layer3Edges()

        Returns
        -------
        pd.DataFrame
            DataFrame containing the Layer 3 Topology.
        """
        return self.session_bf.q.layer3Edges(nodes=self.node).answer().frame()

    def calculate_statistics(self) -> pd.DataFrame:
        """
        Calculates the status and statistical info of the checks.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the statistics.
        """
        is_actual_in_topo_empty = self.actual_not_in_topo.shape[0] == 0
        is_sot_in_topo_empty = self.sot_not_in_topo.shape[0] == 0
        is_topo_in_sot_empty = self.topo_not_in_sot.shape[0] == 0

        error_code, status = (
            (0, "PASSED")
            if is_actual_in_topo_empty and is_sot_in_topo_empty and is_topo_in_sot_empty
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

    def send_results(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Returns Layer 3 topology interfaces.

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
            Layer 3 topology, results, and statistics DataFrames.
        """
        return self.layer3_topo, self.calculate_results(), self.calculate_statistics()
