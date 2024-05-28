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
from customutils import process_stats, dataframe_to_prettytable

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

    data_statistics = dfs.call_method_by_name(func_name, **kwargs)

    return Result(host=task.host, result=data_statistics)


def main():
    """This is the main function which executes all the Nornir Tasks."""
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    bf_session = bfish_init()

    error_result = nr.run(
        name="Erroneous L3 Interface Configuration",
        task=exec_checks,
        bf=bf_session,
        func_name="layer3_check",
        severity_level=logging.INFO,
    )

    # print_result(error_result, vars=["result"])

    #    for host, task_result in error_result.items():
    #        print(
    #            dataframe_to_prettytable(
    #                task_result.result,
    #                title=f"Host:[{host}] Check:Erroneous L3 Interface Configuration",
    #            )
    #        )

    #    for host, task_result in statistics_result.items():
    #        print(
    #            dataframe_to_prettytable(
    #                task_result.result,
    #                title=f"Host:[{host}] Statistics",
    #            )
    #        )

    for host, host_result in error_result.items():
        print(20 * "-" + f"{host}" + 20 * "-")
        print(host_result.result["data"])
        print(50 * "@")
        print(host_result.result["statistics"])

    # for host, task_result in statistics_result.items():
    #    print(task_result.result)
    print(50 * "#")

    tmp = process_stats(error_result)
    print(tmp)

    print_result(error_result["r1"].result, vars=["data"])


# print(
#     dataframe_to_prettytable(
#         tmp,
#         title="Cumulative Statistics",
#     )
# )


if __name__ == "__main__":
    main()
