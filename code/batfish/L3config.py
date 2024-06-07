"""
Name:
-----
    L3config.py

Description:
------------
    Consists of Batfish related classes used for the offline Validation\n
    checks of Layer 3 interfaces.

Classes:
--------
    NodeSession
    NodeL3
    NodeL3Integrity
    NodeL3Topo

Misc variables:
---------------
    __all__\n
    __version__\n
    __author__\n
"""

__all__ = ["NodeSession", "NodeL3", "NodeL3Integrity", "NodeL3Topo"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import List, Dict
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

    def __init__(self, bf: Session, node: str = None):
        """
        Initializes the actual Dataframe with all interface names as a
        result of the bf.q.nodeProperties batfish question for the given
        node. The node parameter derived by the Nornir (task.host.name).

        Parameters
        ----------
        bf: Session
            The already opened batfish Session object used to query the
            batfish service.
        node: str
        The Node or router name used by Nornir (task.host.name).
        """
        self.session_bf = bf
        self.node = node


class NodeL3(NodeSession):
    """
    Keeps L3 interface info for each node.

    Attributes
    ----------
    actual: Batfish DataFrame
        Dataframe keeps the info of L3 interfaces configured in the node.
        This info is fetched by using the build_actual() method.

    sot: Batfish Dataframe
        Dataframe keeps the source of truth for the interfaces. This info
        is fetched  by using the build_sot() method.

    properties: str
        Used to restrict the output info for Batfish question. Defaults to
        'Interface'.

    Methods
    -------
    build_actual()
        Fetches info of all actual configured interfaces of the node.
        It uses the session_bf.q.interfaceProperties() question.

    build_sot()
        Builds a Dataframe representing the Source od Truth for the L3
        interfaces.

    left_anti_join()
        Used to perform checks between DataFrames.

    build_labels()
        Used to build correct labels on various DataFrames. It is used
        by the calculate_results()

    calculate_results()
        Concatenates the various DataFrames of the class in order to
        produce the erroneous results.

    call_method_by_name()
        Used to call a method with its name as a string.
    """

    def __init__(
        self, bf: Session, sot: Dict, node: str = None, properties: str = "Interface"
    ) -> None:
        """
        Parameters
        ----------
        bf: Session
            The already opened batfish Session object used to query the
            batfish service.

        sot: Dict
            The Source of Truth for the node L3 Interfaces.

        node: str
            The  Node or router name used by Nornir (task.host.name).

        properties: str
            Used to restrict the output info for Batfish questions. Defaults
            to 'Interface'.

        """
        super().__init__(bf, node)

        self.properties = properties

        self.actual = self.build_actual()

        self.sot = self.build_sot(source_of_truth=sot)

    def build_actual(self) -> pd.DataFrame:
        """
        Queries the Batfish service by issuing the question
        q.interfaceProperties()

        Returns
        -------
        Dataframe
        The Dataframe for the actually configured L3 Interfaces
        in the node.
        """
        return (
            self.session_bf.q.interfaceProperties(
                nodes=self.node, properties=self.properties
            )
            .answer()
            .frame()
        )

    def build_sot(self, source_of_truth: Dict = None) -> pd.DataFrame:
        """
        Creates the SoT Dataframe for the node L3 Interfaces.

        Parameters
        ----------
        source_of_truth: Dict
            The source of truth for L3 Interfaces.

        Returns
        -------
        Dataframe
        The source of truth Dataframe.
        """
        sot_list = [
            Interface(hostname=self.node, interface=sot_item)
            for sot_item in source_of_truth[self.node]
        ]
        return pd.DataFrame.from_dict({"Interface": sot_list})

    @staticmethod
    def left_anti_join(
        left_df: pd.DataFrame, right_df: pd.DataFrame, properties: str = "Interface"
    ):
        """
        Used to create the Unexpected L3 Interfaces and Missing L3
        Interfaces DataFrame. This is achieved by merging the left_df
        and right_df DataFrames on "Interfaces" column by performing
        LEFT ANTI JOIN.

        Parameters
        ----------
        left_df: pd.DataFrame
            The left dataframe for the LEFT join.
        right_df: pd.DataFrame
            The right dataframe for the LEFT join.
        properties: str
            The common column used for join. Defaults to 'Interface'

        Returns
        -------
        anti_join: Dataframe
            If the left DataFrame is sot and the right one is actual
            then returns the Missing L3 Interfaces. If vice versa
            returns the Unexpected L3 Interfaces.

        """
        outer = pd.merge(
            left_df[[properties]],
            right_df[[properties]],
            how="outer",
            left_on=properties,
            right_on=properties,
            indicator=True,
        )

        anti_join = (
            outer[(outer["_merge"] == "left_only")]
            .drop(columns=["_merge"])
            .reset_index(drop=True)
        )
        return anti_join

    def build_labels(self):
        """
        Builds labels list of DataFrames using the class attribute names.
        This list will be used to concatenate its items in order to build
        the erroneous results for each node.

        Returns
        -------
        List[str] :
            The labels list used for the result DataFrames.
        """
        labels_list = []
        for attribute_name, attribute_value in self.__dict__.items():
            if isinstance(attribute_value, pd.DataFrame):
                df_copy = attribute_value.copy(deep=True)
                df_copy.rename(columns={"Interface": attribute_name}, inplace=True)
                labels_list.append(df_copy)
        return labels_list

    def calculate_results(self):
        """
        DataFrame contains the erroneous elements. This is done
        by merging the attribute DataFrames.

        Returns
        -------
        The DataFrame containing all the above DataFrames.`
        """
        return (
            pd.concat(self.build_labels(), axis=1)
            .reset_index(drop=True)
            .fillna("-", inplace=True)
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


class NodeL3Integrity(NodeL3):
    """
    Calculates the erroneous and  mismatches of L3 Interfaces for the node by
    discovering missing and unexpected interfaces configured on the node.

    Attributes
    ----------
    unexpected: Batfish DataFrame
        Keeps the Interface names which actually configured but not contained
        into SourceOfTruth.

    missing: Batfish DataFrame
        Keeps the Interface names which contained into SourceOfTruth but not
        actually configured on the node.

    Methods
    -------

    calculate_statistics()
        Calculates summary statistics for the node

    send_results()
        Sends result to the Pipeline.
    """

    def __init__(
        self, bf: Session, sot: Dict, node: str = None, properties: str = "Interface"
    ) -> None:

        super().__init__(bf=bf, sot=sot, node=self.node, properties=properties)

        self.unexpected = self.left_anti_join(
            left_df=self.actual, right_df=self.sot, properties=properties
        )

        self.missing = self.left_anti_join(
            left_df=self.sot, right_df=self.actual, properties=properties
        )

    def calculate_statistics(self):
        """Calculates statistics"""
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

    def send_results(self):
        """Returns both erroneous results and statistics"""
        return self.calculate_results(), self.calculate_statistics()


class NodeL3Topo(NodeL3):
    """
    Calculates the Layer3 Topology by querying the batfish
    service. This info will be used to check against SoT
    and the actual configured on the node. The already
    existing attributes self.sot and self.actual will be
    filtered to exclude the Loopback interfaces.

    Attributes
    ----------
    layer3_topo: DataFrame
        Keeps the Layer3 Topology.

    actual_not_in_topo: DataFrame
        Keeps the interfaces configured on the node but not
        exist in Layer3 Topology (if any).

    sot_not_in_topo: DataFrame
        Keeps the interfaces included in the SoT on but not
        exist in Layer3 Topology (if any).

    topo_not_in_sot: DataFrame
        Keeps the interfaces included in Layer3 Topology but
        not exist in the SoT (if any).


    Methods
    -------
    filter_loopback()
        Filters the Loopback interfaces from self.sot and
        self.actual.

    build_layer3_topo()
        Loads the Layer3 Topology DataFrame.

    calculate_statistics()
        Calculates summary statistics for the node checks.

    get_topo(self)
        Returns the info needed by pipeline.

    """

    def __init__(
        self, bf: Session, sot: Dict, node: str = None, properties: str = "Interface"
    ) -> None:

        super().__init__(bf=bf, sot=sot, node=self.node, properties=properties)

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

    def filter_loopback(self) -> None:
        """
        Eliminates the Loopback interface from both self.sot and
        sot.actual DataFrames

        Returns
        self.sot, self.actual  DataFrames
            Without Loopback interfaces.
        """
        sot = self.sot[
            self.sot.apply(
                lambda row: not row["Interface"].interface.startswith("Loop"),
                axis=1,
            )
        ]

        actual = self.actual[
            self.actual.apply(
                lambda row: row["Interface"].hostname == self.node
                and not row["Interface"].interface.startswith("Loop"),
                axis=1,
            )
        ]
        return sot, actual

    def build_layer3_topo(self) -> pd.DataFrame:
        """
        Builds the Layer3 Topo for the node by calling the batfish question
        q.layer3Edges()

        Returns
        -------
        self.layer3_topo: DataFrame
        returns the Layer3 info for the node in order to be kept in the attribute
        self.layer3_topo
        """
        return self.session_bf.q.layer3Edges(nodes=self.node).answer().frame()

    def calculate_statistics(self):
        """
        Calculates the status and statistical info of the checks. The
        status of the check is PASSED if the missing and unexpected
        DataFrames are empty, otherwise the status is FAILED.

        Returns
        -------
        stats: DataFrame
            The statistical DataFrame of the check.
        """
        c1 = self.actual_not_in_topo.shape[0] == 0
        c2 = self.sot_not_in_topo.shape[0] == 0
        c3 = self.topo_not_in_sot.shape[0] == 0

        error_code, status = (0, "PASSED") if c1 and c2 and c3 else (-1, "FAILED")

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
            self.calculate_results(),
            self.calculate_statistics(),
        )
