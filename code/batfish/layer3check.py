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
from toponodel3 import L3TopoNode

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

    device = L3TopoNode(
        bf=bf,
        node=f"{task.host.name}",
    )

    res = device.call_method_by_name(func_name, **kwargs)
    data = dfprint(
        df=res,
        props=["#"] + list(res.columns),
        title=f"Host=[{task.host.name}]/" + title,
    )
    # print(res)
    return Result(host=task.host, result=data)


def main():
    """This is the main function which executes all the Nornir Tasks."""
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    bf_session = bfish_init()

    result = nr.run(
        name="Erroneous L3 Interface Configuration",
        task=exec_checks,
        bf=bf_session,
        func_name="layer3_erroneous",
        nodedict=ifaces,
        title="Erroneous L3 Interface Configuration",
        severity_level=logging.INFO,
    )

    print_result(result)


if __name__ == "__main__":
    main()
