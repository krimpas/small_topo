"""
Name:
-----
    L3config.py

Description:
------------
    Consists of Batfish related classes used for the offline Validation
    checks of Layer 3 interfaces.

Classes:
--------
    NodeSession
    NodeL3
    NodeL3Integrity
    NodeL3Topo

Misc variables:
---------------
    __all__
    __version__
    __author__
"""

__all__ = ["NodeSession", "NodeL3", "NodeL3Integrity", "NodeL3Topo"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import List, Dict, Optional, Tuple
import pandas as pd
from pybatfish.client.session import Session
from pybatfish.datamodel import Interface


class NodeSession:
    """
    Keeps a Batfish session and the Node name as a Nornir task.host.name

    Attributes
    ----------
    bf: Session
        An already open batfish Session object used to query the batfish
        service.

    node: str
        The name of the device as Nornir Task Host Name to receive
        (task.host.name)
    """

    def __init__(self, bf: Session, node: Optional[str] = None):
        self.session_bf = bf
        self.node = node


class NodeL3(NodeSession):
    """
    Keeps L3 interface info for each node.

    Attributes
    ----------
    actual: pd.DataFrame
        DataFrame that keeps the info of L3 interfaces configured in the node.
        This info is fetched by using the build_actual() method.

    sot: pd.DataFrame
        DataFrame that keeps the source of truth for the interfaces. This info
        is fetched by using the build_sot() method.

    properties: str
        Used to restrict the output info for Batfish questions. Defaults to 'Declared_Names'.
    """

    def __init__(
        self,
        bf: Session,
        sot: Dict,
        node: Optional[str] = None,
        properties: str = "Declared_Names",
    ) -> None:
        super().__init__(bf, node)
        self.properties = properties
        self.actual = self.build_actual()
        self.sot = self.build_sot(source_of_truth=sot)

    def build_actual(self) -> pd.DataFrame:
        """
        Queries the Batfish service by issuing the question q.interfaceProperties()

        Returns
        -------
        pd.DataFrame
            The DataFrame for the actually configured L3 Interfaces in the node.
        """
        return (
            self.session_bf.q.interfaceProperties(
                nodes=self.node, properties=self.properties
            )
            .answer()
            .frame()
        )

    def build_sot(self, source_of_truth: Dict) -> pd.DataFrame:
        """
        Creates the SoT DataFrame for the node L3 Interfaces.

        Parameters
        ----------
        source_of_truth: Dict
            The source of truth for L3 Interfaces.

        Returns
        -------
        pd.DataFrame
            The source of truth DataFrame.
        """
        sot_list = [
            Interface(hostname=self.node, interface=sot_item)
            for sot_item in source_of_truth[self.node]
        ]
        return pd.DataFrame.from_dict({"Interface": sot_list})

    @staticmethod
    def left_anti_join(
        left_df: pd.DataFrame, right_df: pd.DataFrame, properties: str = "Interface"
    ) -> pd.DataFrame:
        """
        Performs a left anti join to identify missing and unexpected interfaces.

        Parameters
        ----------
        left_df: pd.DataFrame
            The left DataFrame for the join.
        right_df: pd.DataFrame
            The right DataFrame for the join.
        properties: str
            The column used for the join. Defaults to 'Interface'.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the results of the left anti join.
        """
        outer = pd.merge(
            left_df[[properties]], right_df[[properties]], how="outer", indicator=True
        )
        anti_join = (
            outer[outer["_merge"] == "left_only"]
            .drop(columns=["_merge"])
            .reset_index(drop=True)
        )
        return anti_join

    def build_labels(self, excluded: List[str]) -> List[pd.DataFrame]:
        """
        Builds a list of DataFrames for concatenation.

        Parameters
        ----------
        excluded: List[str]
            List of attributes to exclude.

        Returns
        -------
        List[pd.DataFrame]
            List of DataFrames for concatenation.
        """
        labels_list = []
        for attribute_name, attribute_value in self.__dict__.items():
            if (
                isinstance(attribute_value, pd.DataFrame)
                and attribute_name not in excluded
            ):
                df_copy = attribute_value.copy(deep=True)
                df_copy.rename(columns={"Interface": attribute_name}, inplace=True)
                labels_list.append(df_copy)
        return labels_list

    def calculate_results(self) -> pd.DataFrame:
        """
        Concatenates DataFrames to produce the erroneous results.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the erroneous results.
        """
        excluded = ["actual", "Declared_Names"]
        labels = self.build_labels(excluded=excluded)
        result_df = pd.concat(labels, axis=1).reset_index(drop=True)
        result_df.fillna("-", inplace=True)
        return result_df

    def call_method_by_name(self, name: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        Dynamically calls a class method by its name.

        Parameters
        ----------
        name: str
            The method name.
        kwargs: dict
            The method parameters.

        Returns
        -------
        Optional[pd.DataFrame]
            The result of the method call.
        """
        method = getattr(self, name, None)
        if method:
            return method(**kwargs)
        return None


class NodeL3Integrity(NodeL3):
    """
    Calculates erroneous and mismatched L3 Interfaces for the node.

    Attributes
    ----------
    unexpected: pd.DataFrame
        Interfaces actually configured but not in SoT.

    missing: pd.DataFrame
        Interfaces in SoT but not actually configured on the node.
    """

    def __init__(
        self,
        bf: Session,
        sot: Dict,
        node: Optional[str] = None,
        properties: str = "Declared_Names",
    ) -> None:
        super().__init__(bf=bf, sot=sot, node=node, properties=properties)
        self.unexpected = self.left_anti_join(
            left_df=self.actual, right_df=self.sot, properties="Interface"
        )
        self.missing = self.left_anti_join(
            left_df=self.sot, right_df=self.actual, properties="Interface"
        )

    def calculate_statistics(self) -> pd.DataFrame:
        """
        Calculates summary statistics for the node.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the statistics.
        """
        is_missing_empty = self.missing.shape[0] == 0
        is_unexpected_empty = self.unexpected.shape[0] == 0

        error_code, status = (
            (0, "PASSED")
            if is_missing_empty and is_unexpected_empty
            else (-1, "FAILED")
        )

        stats = {
            "retcode": [error_code],
            "SoT": [self.sot.shape[0]],
            "Unexpected": [self.unexpected.shape[0]],
            "Missing": [self.missing.shape[0]],
            "Status": [status],
        }
        return pd.DataFrame.from_dict(stats)

    def send_results(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Returns both erroneous results and statistics.

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame]
            The results and statistics DataFrames.
        """
        return self.calculate_results(), self.calculate_statistics()


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
