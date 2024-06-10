"""
Name:
-----
    nodel3.py

Description:
------------
    Consists of NodeL3 class which queries the batfish service to
    fetch informationProperties. Based on the results the Class
    keeps info for the SoT and the actual configured L3 Interfaces
    on the node.  

Classes:
--------
    NodeL3

Misc variables:
---------------
    __all__
    __version__
    __author__
"""

__all__ = ["NodeL3"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import List, Dict, Optional
import pandas as pd
from pybatfish.client.session import Session
from pybatfish.datamodel import Interface
from .nodesession import NodeSession

DEFAULT_SOT_KEYS = [
    "description",
    "enabled",
    "ipv4",
    "mask",
    "mtu",
]


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
            Interface(hostname=self.node, interface=iface["name"].replace(" ", ""))
            for iface in source_of_truth[self.node]["interfaces"]
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

    def calculate_results(self, excluded: List[str]) -> pd.DataFrame:
        """
        Concatenates DataFrames to produce the erroneous results.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the erroneous results.
        """

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
