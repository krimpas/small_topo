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
from L3check2 import dfprint
from toponodel3 import NodeSection, TopoNodeL3Interface

ifaces = {
    "r1": ["GigabitEthernet2", "GigabitEthernet4", "Loopback0"],
    "r2": ["GigabitEthernet2", "GigabitEthernet3", "GigabitEthernet4", "Loopback0"],
    "r3": ["GigabitEthernet2", "GigabitEthernet3", "Loopback0"],
    "r4": ["GigabitEthernet0/1", "Loopback0"],
    "r5": ["GigabitEthernet0/1", "GigabitEthernet0/2", "Loopback0", "Loopback5"],
}

load_dotenv()


def exec_checks(
    task: Task, bf: Session, func_name: str = "", title: str = "", **kwargs
) -> Result:
    """mplah"""

    device = NodeSection(bf=bf, node=f"{task.host.name}", properties="Interfaces")

    dfs = TopoNodeL3Interface(sot=ifaces[device.node], actual_df=device.actual)

    erroneous, stats = dfs.call_method_by_name(func_name, **kwargs)

    # erroneous_data = dfprint(
    #    df=erroneous,
    #    props=["#"] + list(erroneous.columns),
    #    title=f"Host=[{task.host.name}]/" + title,
    # )
    stats.insert(0, "Device", [f"{task.host.name}"], True)
    # stats_data = dfprint(
    #    df=stats,
    #    props=["#"] + list(stats.columns),
    #    title=f"Host=[{task.host.name}]/" + title,
    # )
    return Result(host=task.host, data=erroneous, statistics=stats)


def main():
    """This is the main function which executes all the Nornir Tasks."""
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    bf_session = bfish_init()

    result = nr.run(
        name="Erroneous L3 Interface Configuration",
        task=exec_checks,
        bf=bf_session,
        func_name="layer3_check",
        title="Erroneous L3 Interface Configuration",
        severity_level=logging.INFO,
    )
    tmp_list_df = []
    for h in nr.inventory.hosts.keys():
        print(result[h].data)
        print("----------------------------------------------")
        tmp_list_df.append(result[h].statistics)

    tmp_df = pd.concat(tmp_list_df, axis=0)
    print(tmp_df.reset_index(drop=True))

    print_result(result.any(), vars=["data", "statistics"])


if __name__ == "__main__":
    main()
