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
from nornir_utils.plugins.functions import print_result
from dotenv import load_dotenv
from bfish_init import bfish_init
from pybatfish.client.session import Session
from toponodel3 import NodeSection, TopoNodeL3Interface
from prettytable import PrettyTable

ifaces = {
    "r1": ["GigabitEthernet2", "GigabitEthernet4", "Loopback0"],
    "r2": ["GigabitEthernet2", "GigabitEthernet3", "GigabitEthernet4", "Loopback0"],
    "r3": ["GigabitEthernet2", "GigabitEthernet3", "Loopback0"],
    "r4": ["GigabitEthernet0/1", "Loopback0"],
    "r5": ["GigabitEthernet0/1", "GigabitEthernet0/2", "Loopback0", "Loopback5"],
}

load_dotenv()


def exec_checks(task: Task, bf: Session, func_name: str = "", **kwargs) -> Result:
    """mplah"""

    device = NodeSection(bf=bf, node=f"{task.host.name}", properties="Interfaces")

    dfs = TopoNodeL3Interface(sot=ifaces[device.node], actual_df=device.actual)

    result_data = dfs.call_method_by_name(func_name, **kwargs)

    return Result(host=task.host, result=result_data)


def process_stats(nr, result):
    """Stas processing"""

    for h in nr.inventory.hosts.keys():
        result[h].insert(0, "Device", [f"{h}"], True)

    tmp_list_df = []
    for h in nr.inventory.hosts.keys():
        tmp_list_df.append(result[h])

    tmp_df = pd.concat(tmp_list_df, axis=0)
    tmp = tmp_df.reset_index(drop=True)

    return tmp


def dataframe_to_prettytable(
    df: pd.DataFrame, title: str = "Error Elements"
) -> PrettyTable:
    """Creates a Pretty Table from a Dataframe"""
    # Create PrettyTable object
    table = PrettyTable()

    if df is not None:
        # Add columns
        table.field_names = ["#"] + df.columns.tolist()
        # Add rows
        for row in df.itertuples():
            table.add_row(row)

    return table.get_string(title=title)


def main():
    """This is the main function which executes all the Nornir Tasks."""
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    bf_session = bfish_init()

    error_result = nr.run(
        name="Erroneous L3 Interface Configuration",
        task=exec_checks,
        bf=bf_session,
        func_name="layer3_erroneous",
        severity_level=logging.INFO,
    )

    statistics_result = nr.run(
        name="Statistics Results",
        task=exec_checks,
        bf=bf_session,
        func_name="layer3_statistics",
        severity_level=logging.INFO,
    )

    for host, task_result in error_result.items():
        print(
            dataframe_to_prettytable(
                task_result.result,
                title=f"Host:[{host}] Check:Erroneous L3 Interface Configuration",
            )
        )

    for host, task_result in statistics_result.items():
        print(
            dataframe_to_prettytable(
                task_result.result,
                title=f"Host:[{host}] Statistics",
            )
        )

    # tmp = process_stats(nr, statistics_result)
    # print(tmp)
    for host, task_result in statistics_result.items():
        print(task_result)


if __name__ == "__main__":
    main()
