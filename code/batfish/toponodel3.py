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
    NodeSession\n
    NodeSection\n
    TopoNodeL3Interface\n

Misc variables:
---------------
    __all__\n
    __version__\n
    __author__\n
"""

__all__ = ["NodeSession", "NodeSection", "TopoNodeL3Interface"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import List
import pandas as pd
from pybatfish.client.session import Session


class NodeSession:
    """
    Keeps a Batfish session and the Node name as a Nornir task.host.name\n

    Attributes
    ----------
    bf: Session
        An already open batfish Session object used to query the batfish\n
        service.

    node: str
        The name of the device as Nornir Task Host Name to receive\n
        (task.host.name)

    """

    def __init__(self, bf: Session, node: str = None):
        """
        Initializes the actual Dataframe with all interface names\n
        as a result of the bf.q.nodeProperties batfish question for the\n
        given node. The node parameter derived by using the Nornir\n
        (task.host.name).\n

        Parameters
        ----------
        bf: Session
            The already opened batfish Session object used to query the\n
            batfish service.
        node: str
            The Node or router name used by Nornir (task.host.name).\n
        """
        self.session_bf = bf

        self.node = node


class NodeSection(NodeSession):
    """
    Keeps an individual config section of each node.

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
        self.configured = (
            self.session_bf.q.nodeProperties(nodes=node, properties=properties)
            .answer()
            .frame()
        )

        # Transform the info fetched into a dataframe
        self.actual = pd.DataFrame({properties: self.configured.iloc[0][properties]})


class TopoNodeL3Interface:
    """
    Keeps all L3 Interfaces names of the specified node and \n
    the SourceOfTruth. Then the unexpected and missing L3\n
    interfaces are calculated.\n

    Attributes
    ----------
    layer3_actual: Batfish DataFrame
        Keeps the Interface Names as a result of the Batfish Query.\n
    layer3_sot: Batfish DataFrame
        Keeps the Interface names based on SourceOfTruth.\n
    layer3_unexpected: Batfish DataFrame
        Keeps the Interface names which actually configured but \n
        not contained into SourceOfTruth.\n
    layer3_missing: Batfish DataFrame
        Keeps the Interface names which contained into SourceOfTruth\n
        but not actually configured.\n

    Methods
    -------
    _build_sot()
        Creates the SoT Dataframe for the L3 Interfaces.\n
    _build_erroneous_layer3()
        Used to create the Unexpected L3 Interfaces DataFrame and the\n
        Missing L3 Interfaces DataFrame.
    layer3_erroneous()
        Builds a Dataframe by merging all the above Dataframes.

    """

    def __init__(self, sot: List, actual_df: pd.DataFrame):
        """
        Initialization of the 4 DataFrames needed:\n
        1. SoT of L3 Interfaces.\n
        2. Actually configured L3 Interfaces.\n
        3. Unexpected configured L3 Interfaces.\n
        4. Missing L3 Interfaces.\n

        Parameters
        ----------
        sot: List
            Points to the source of truth of Interfaces for the\n
            specified node.
        actual: Batfish Dataframe
            Represents the names of all configured L3 interfaces\n
            of the specified node.

        """
        self.layer3_actual = actual_df

        self.layer3_sot = self._build_sot(source_of_truth=sot)

        self.layer3_unexpected = self._build_erroneous_layer3(
            left_df=self.layer3_actual, right_df=self.layer3_sot
        )

        self.layer3_missing = self._build_erroneous_layer3(
            left_df=self.layer3_sot, right_df=self.layer3_actual
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
        return pd.DataFrame({"Interfaces": source_of_truth})

    def _build_erroneous_layer3(self, left_df: pd.DataFrame, right_df: pd.DataFrame):
        """
        Used to create the Unexpected L3 Interfaces and Missing L3\n
        Interfaces DataFrame. This is achieved by merging the left_df\n
        and right_df DataFrames on "Interfaces" column by performing\n
        LEFT JOIN.

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
        erroneous_ifaces = pd.merge(
            left_df,
            right_df,
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

    def layer3_statistics(self):
        """
        Calculates the status and statistical info of the checks. The
        status of the check is PASSED if the missing and unexpected
        DataFrames are empty, otherwise the status is FAILED.

        Returns
        -------
        stats: DataFrame
            The statistical DataFrame of the check.
        """
        is_missing_empty = self.layer3_missing.shape[0] == 0
        is_unexpected_empty = self.layer3_unexpected.shape[0] == 0

        error_code, status = (
            (0, "PASSED")
            if is_missing_empty and is_unexpected_empty
            else (-1, "FAILED")
        )

        stats = {
            "retcode": [error_code],
            "Unexpected": [self.layer3_unexpected.shape[0]],
            "Missing": [self.layer3_missing.shape[0]],
            "Status": [status],
        }
        return pd.DataFrame(stats)

    def layer3_erroneous(self):
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

        tmp_sot = self.layer3_sot.copy()
        tmp_sot.rename(columns={"Interfaces": "SoT"}, inplace=True)

        tmp_actual = self.layer3_actual.copy()
        tmp_actual.rename(columns={"Interfaces": "Actual"}, inplace=True)

        tmp_unexpected = self.layer3_unexpected.copy()
        tmp_unexpected.rename(columns={"Interfaces": "Unexpected"}, inplace=True)

        tmp_missing = self.layer3_missing.copy()
        tmp_missing.rename(columns={"Interfaces": "Missing"}, inplace=True)

        tmp_erroneous = pd.concat(
            [tmp_sot, tmp_actual, tmp_unexpected, tmp_missing], axis=1
        ).reset_index(drop=True)

        tmp_erroneous.fillna("-", inplace=True)

        return tmp_erroneous

    def layer3_check(self):
        """
        Returns the Dataframe of errors and the statistics.

        Returns
        -------
        layer3_erroneous: DataFrame
            The DataFrame contains the erroneous elements
        layer3_statistics: DataFrame
            The DataFrame contains the statistics elements
        """
        return self.layer3_erroneous(), self.layer3_statistics()

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
