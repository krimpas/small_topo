"""
This file contains all functions needed in order to let the
Nornir tasks.
"""

import os
import logging
from l3info import NodeL3InterfaceInfo
from bfish_L3iface_props import BFISH_L3IFACE_PROPS
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from dotenv import load_dotenv
from bfish_init import bfish_init
from pybatfish.client.session import Session
from L3check2 import dfprint

load_dotenv()


def exec_checks(task: Task, bf: Session, func_name: str = "", **kwargs) -> Result:
    """mplah"""

    device = NodeL3InterfaceInfo(
        bf=bf,
        node=f"{task.host.name}",
        properties=BFISH_L3IFACE_PROPS.select_properties(),
    )

    res = device.call_method_by_name(func_name, **kwargs)

    data = dfprint(df=res, props=["#"] + list(res.columns), title=func_name)

    return Result(host=task.host, result=data)


def main():
    """This is the main function which executes all the Nornir Tasks."""
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    bf_session = bfish_init()

    # Run the validation task on all filtered hosts
    # result = nr.run(
    #     name="L3 Loopback Batfish checks",
    #     task=exec_checks,
    #     bf=bf_session,
    #     func_name="check_layer3_interface",
    #     anet="172.16.0.0/12",
    #     ifacetype="Loop",
    #     severity_level=logging.INFO,
    # )

    # Print the results
    # print_result(result)

    # result = nr.run(
    #    name="Fetching Interfaces",
    #    task=exec_checks,
    #    bf=bf_session,
    #    func_name="lookup_layer3_interface",
    #    severity_level=logging.INFO,
    # )

    # Print the results
    # print_result(result)

    result = nr.run(
        name="All Interfaces",
        task=exec_checks,
        bf=bf_session,
        func_name="all_layer3_interfaces",
        severity_level=logging.INFO,
    )

    # Print the results
    print_result(result)

    result = nr.run(
        name="Node Interfaces",
        task=exec_checks,
        bf=bf_session,
        func_name="all_node_configured_interfaces",
        severity_level=logging.INFO,
    )

    # Print the results
    print_result(result)

    result = nr.run(
        name="Missing and Unexpected Interfaces",
        task=exec_checks,
        bf=bf_session,
        func_name="missing_and_unexpected",
        severity_level=logging.INFO,
    )

    # Print the results
    print_result(result)


if __name__ == "__main__":
    main()
