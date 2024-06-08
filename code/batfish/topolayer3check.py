"""
This file contains all functions needed in order to let the
Nornir tasks.
"""

import os
import logging
from bfish_L3iface_props import BFISH_L3IFACE_PROPS
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result, print_title
from dotenv import load_dotenv
from bfish_init import bfish_init
from pybatfish.client.session import Session
from customutils import process_stats, dataframe_to_prettytable, echo_nornir_result
from L3.nodel3topo import NodeL3Topo


ifaces = {
    "r1": ["GigabitEthernet2", "GigabitEthernet4", "Loopback0"],
    "r2": ["GigabitEthernet2", "GigabitEthernet3", "GigabitEthernet4", "Loopback0"],
    "r3": ["GigabitEthernet2", "GigabitEthernet3", "Loopback0"],
    "r4": ["GigabitEthernet0/1", "GigabitEthernet3", "Loopback0"],
    "r5": ["GigabitEthernet0/1", "GigabitEthernet0/2", "Loopback0", "Loopback5"],
}

load_dotenv()


def exec_topo(task: Task, bf: Session, func_name: str = "", **kwargs) -> Result:
    """mplah"""

    device = NodeL3Topo(
        bf=bf,
        sot=ifaces,
        node=f"{task.host.name}",
        properties="Declared_Names",
    )

    topo, data, statistics = device.call_method_by_name(func_name, **kwargs)

    return Result(
        host=task.host, result=dict(topo=topo, data=data, statistics=statistics)
    )


def main():
    """This is the main function which executes all the Nornir Tasks."""
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    # Initialize Batfish session
    bf_session = bfish_init()

    topo_result = nr.run(
        name="Erroneous L3 Topology Configuration",
        task=exec_topo,
        bf=bf_session,
        func_name="send_results",
        severity_level=logging.INFO,
    )
    for h, res in topo_result.items():
        print_title(f"Host=[{h}]=>L3 Topology")
        print(res.result["topo"])
        print_title(f"Host=[{h}]=>L3 Topo Errors")
        print(res.result["data"])
        print_title(f"Host=[{h}]=>L3 Topo statistics")
        print(res.result["statistics"])
        print(80 * "+")

    print(80 * "#")
    print_title("Total Summary Statistics for all Hosts")
    tmp_df = process_stats(topo_result)

    tmp_pt = dataframe_to_prettytable(tmp_df, title="Summary Statistics")
    print(tmp_pt)
    print_title("END: Total Summary Statistics for all Hosts")
    print(80 * "#")
    # print(80 * "+")
    # print_result(topo_result)
    # print(80 * "+")


if __name__ == "__main__":
    main()
