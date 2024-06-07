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
from toponodel3 import NodeSection, NodeL3Interface
from customutils import process_stats, dataframe_to_prettytable, echo_nornir_result
from typing import List
from pprint import pprint
from L3config import NodeL3Integrity

ifaces = {
    "r1": ["GigabitEthernet2", "GigabitEthernet4", "Loopback0"],
    "r2": ["GigabitEthernet2", "GigabitEthernet3", "GigabitEthernet4", "Loopback0"],
    "r3": ["GigabitEthernet2", "GigabitEthernet3", "Loopback0"],
    "r4": ["GigabitEthernet0/1", "GigabitEthernet3", "Loopback0"],
    "r5": ["GigabitEthernet0/1", "GigabitEthernet0/2", "Loopback0", "Loopback5"],
}

load_dotenv()


def exec_checks(task: Task, bf: Session, func_name: str = "", **kwargs) -> Result:
    """mplah"""

    # device = NodeSection(bf=bf, node=f"{task.host.name}", properties="Interfaces")

    # dfs = NodeL3Interface(sot=ifaces[device.node], actual_df=device.actual)

    dev = NodeL3Integrity(
        bf=bf, sot=ifaces, node=f"{task.host.name}", properties="Interfaces"
    )

    data, stats = dev.call_method_by_name(func_name, **kwargs)

    return Result(host=task.host, result=dict(data=data, statistics=stats))


def main():
    """This is the main function which executes all the Nornir Tasks."""
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    # Initialize Batfish session
    bf_session = bfish_init()

    error_result = nr.run(
        name="Erroneous L3 Interface Configuration",
        task=exec_checks,
        bf=bf_session,
        func_name="send_results",
        severity_level=logging.INFO,
    )
    print(80 * "@")
    for h, res in error_result.items():
        print_title(f"Host=[{h}]=>Erroneous L3 Interface Configuration")
        print(res.result["data"])
        print_title(f"Host=[{h}]=>Host Statistics")
        print(res.result["statistics"])
        print(80 * "+")

    # echo_nornir_result(error_result, title="L3 Interfaces Conf")

    print_title("Total Summary Statistics for all Hosts")
    tmp_df = process_stats(error_result)

    tmp_pt = dataframe_to_prettytable(tmp_df, title="Summary Statistics")
    print(tmp_pt)
    print_title("END: Total Summary Statistics for all Hosts")


if __name__ == "__main__":
    main()
