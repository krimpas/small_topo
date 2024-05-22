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

from typing import Dict, List
import pandas as pd
from pybatfish.client.session import Session


class L3TopoNode:
    """
    Keeps the L3 configured interface names of a given network node. \n

    Performs the bf.q.nodeProperties question to the batfish service \n
    in order to fetch all interface names as s list of strings for the\n
    node specified. This Class will be used by. \n

    Attributes
    ----------
    bf: Session
        An already open batfish Session object used to query the batfish\n
        service.

    node: str
        The name of the device as Nornir Task Host Name to receive\n
        (task.host.name)

    layer3_topo: Batfish Dataframe
        Keeps the dataframe L3 topology elements of the specified node as\n
        a result of bf.q.layer3Edges batfish question.

    Methods
    -------

    """

    def __init__(self, bf: Session, node: str = "") -> None:
        """
        Initializes the actual Dataframe with all interface names\n
        as a result of the bf.q.nodeProperties batfish question for the\n
        given node. The node parameter derived by using the Nornir\n
        (task.host.name).\n

        Parameters
        ----------
        bf: Session
            The already opened batfish Session object used to query the
            batfish service.
        node: str
            The  Node or router name used by Nornir (task.host.name).
        configured: List[str]
            A list of interface names as strings
        actual: DataFrame
            Dataframe derived from the list of interface names (configured)

        Returns
        -------
        None
        """
        self.session_bf = bf
        #
        self.node = node

        self.configured = (
            self.session_bf.q.nodeProperties(nodes=node, properties="Interfaces")
            .answer()
            .frame()
        )

        self.actual = pd.DataFrame(
            {"Interfaces": self.configured.iloc[0]["Interfaces"]}
        )


class L3NodeConf:
    """ """

    def __init__(self, sot: List, actual_df: pd.DataFrame):
        """ """
        self.layer3_actual = actual_df

        self.layer3_sot = self._build_sot(source_of_truth=sot)

        self.layer3_unexpected = self._build_erroneous_layer3(
            left_df=self.layer3_actual, right_df=self.layer3_sot
        )

        self.layer3_missing = self._build_erroneous_layer3(
            left_df=self.layer3_sot, right_df=self.layer3_actual
        )

    def _build_sot(self, source_of_truth: List = None):
        """ """
        return pd.DataFrame({"Interfaces": source_of_truth)

    def _build_erroneous_layer3(self, left_df: pd.DataFrame, right_df: pd.DataFrame):
        """ """
        erroneous_ifaces = pd.merge(
            left_df,
            right_df[["Interfaces"]],
            on="Interfaces",
            how="left",
            indicator=True,
        )

        erroneous_ifaces = (
            erroneous_ifaces[erroneous_ifaces["_merge"] == "left_only"]
            .drop(columns=["_merge"])
            .reset_index(drop=True)
        )

        return erroneous_ifaces

    def layer3_erroneous(self):
        """builds a Dataframe"""

        tmp_sot = self.layer3_sot
        tmp_sot.rename(columns={"Interfaces": "SoT"}, inplace=True)

        tmp_actual = self.layer3_actual
        tmp_actual.rename(columns={"Interfaces": "Actual"}, inplace=True)

        tmp_unexpected = self.layer3_unexpected
        tmp_unexpected.rename(columns={"Interfaces": "Unexpected"}, inplace=True)

        tmp_missing = self.layer3_missing
        tmp_missing.rename(columns={"Interfaces": "Missing"}, inplace=True)

        tmp_erroneous = pd.concat(
            [tmp_sot, tmp_actual, tmp_unexpected, tmp_missing], axis=1
        )
        tmp_erroneous.fillna("-", inplace=True)

        return tmp_erroneous

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
