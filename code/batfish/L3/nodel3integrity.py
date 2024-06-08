"""
Name:
-----
    nodel3integrity.py

Description:
------------
    Consists of the NodeL3Integrity class which calculates all mismatches
    related to the Layer 3 interfaces on to the node.

Classes:
--------
    NodeL3Integrity

Misc variables:
---------------
    __all__
    __version__
    __author__
"""

__all__ = ["NodeL3Integrity"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import Dict, Optional, Tuple
import pandas as pd
from pybatfish.client.session import Session
from .nodel3 import NodeL3


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
        return (
            self.calculate_results(excluded=["actual", "Declared_Names"]),
            self.calculate_statistics(),
        )
