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
from L3.nodel3integrity import NodeL3Integrity


ifaces = {
    "r1": {
        "interfaces": [
            {
                "description": "towards OSPF area 0",
                "enabled": True,
                "ipv4": "10.0.0.1",
                "mask": "255.255.255.240",
                "mtu": 1500,
                "name": "GigabitEthernet 2",
                "ospf_config": {
                    "area": "0.0.0.0",
                    "cost": 9,
                    "net_type": "broadcast",
                    "priority": 255,
                },
            },
            {
                "description": "towards OSPF area 51",
                "enabled": True,
                "ipv4": "10.123.34.1",
                "mask": "255.255.255.224",
                "mtu": 1500,
                "name": "GigabitEthernet 4",
            },
            {
                "enabled": True,
                "ipv4": "172.16.1.1",
                "mask": "255.255.255.0",
                "name": "Loopback 0",
                "ospf_config": {"area": "0.0.0.1", "net_type": "point-to-point"},
            },
        ]
    },
    "r2": {
        "interfaces": [
            {
                "description": "towards OSPF area 0",
                "enabled": True,
                "ipv4": "10.0.0.2",
                "mask": "255.255.255.240",
                "mtu": 1500,
                "name": "GigabitEthernet 2",
                "ospf_config": {"cost": 10, "net_type": "broadcast", "priority": 254},
            },
            {
                "description": "towards r4/OSPF Area 0.0.2.4",
                "enabled": True,
                "ipv4": "10.0.24.2",
                "mask": "255.255.255.248",
                "mtu": 1500,
                "name": "GigabitEthernet 3",
                "ospf_config": {"net_type": "point-to-point"},
            },
            {
                "description": "towards r5/OSPF area 0.0.2.5",
                "enabled": True,
                "ipv4": "10.0.25.2",
                "mask": "255.255.255.248",
                "mtu": 1500,
                "name": "GigabitEthernet 4",
                "ospf_config": {"net_type": "point-to-point"},
            },
            {
                "enabled": True,
                "ipv4": "172.16.2.2",
                "mask": "255.255.255.0",
                "name": "Loopback 0",
                "ospf_config": {"area": "0.0.0.0", "net_type": "point-to-point"},
            },
        ]
    },
    "r3": {
        "interfaces": [
            {
                "description": "towards OSPF area 0",
                "enabled": True,
                "ipv4": "10.0.0.3",
                "mask": "255.255.255.240",
                "mtu": 1500,
                "name": "GigabitEthernet 2",
                "ospf_config": {
                    "area": "0.0.0.0",
                    "net_type": "broadCAST",
                    "priority": 0,
                },
            },
            {
                "description": "towards r5/OSPF area 0.0.3.5",
                "enabled": True,
                "ipv4": "10.0.35.3",
                "mask": "255.255.255.248",
                "mtu": 1500,
                "name": "GigabitEthernet 3",
                "ospf_config": {
                    "area": "0.0.3.5",
                    "key_chain": "area0.0.3.5",
                    "net_type": "point-to-point",
                },
            },
            {
                "enabled": True,
                "ipv4": "172.16.3.3",
                "mask": "255.255.255.0",
                "name": "Loopback 0",
                "ospf_config": {"area": "0.0.0.3", "net_type": "point-to-point"},
            },
        ]
    },
    "r4": {
        "interfaces": [
            {
                "description": "towards r2/OSPF Area 0.0.2.4",
                "enabled": True,
                "ipv4": "10.0.24.4",
                "mask": "255.255.255.248",
                "mtu": 1500,
                "name": "GigabitEthernet 0/1",
                "ospf_config": {"area": "0.0.2.4", "net_type": "point-to-point"},
            },
            {
                "enabled": True,
                "ipv4": "172.16.4.4",
                "mask": "255.255.255.0",
                "name": "Loopback 0",
                "ospf_config": {"area": "0.0.2.4", "net_type": "point-to-point"},
            },
        ]
    },
    "r5": {
        "interfaces": [
            {
                "description": "towards r2/OSPF area 0.0.2.4",
                "enabled": True,
                "ipv4": "10.0.25.5",
                "mask": "255.255.255.248",
                "mtu": 1500,
                "name": "GigabitEthernet 0/1",
                "ospf_config": {"net_type": "point-to-point"},
            },
            {
                "description": "towards r3/OSPF area 0.0.3.5",
                "enabled": True,
                "ipv4": "10.0.35.5",
                "mask": "255.255.255.248",
                "mtu": 1500,
                "name": "GigabitEthernet 0/2",
                "ospf_config": {
                    "key_chain": "area 0.0.3.5",
                    "net_type": "point-to-point",
                },
            },
            {
                "description": "just loopback ",
                "enabled": True,
                "ipv4": "172.16.5.5",
                "mask": "255.255.255.0",
                "name": "Loopback 0",
                "ospf_config": {"net_type": "point-to-point"},
            },
            {
                "description": "just loopback 1",
                "enabled": False,
                "ipv4": "172.16.55.55",
                "mask": "255.255.255.0",
                "name": "Loopback 5",
                "ospf_config": {"net_type": "point-to-point"},
            },
        ]
    },
}
load_dotenv()


def exec_checks(task: Task, bf: Session, func_name: str = "", **kwargs) -> Result:
    """mplah"""

    # device = NodeSection(bf=bf, node=f"{task.host.name}", properties="Interfaces")

    # dfs = NodeL3Interface(sot=ifaces[device.node], actual_df=device.actual)

    dev = NodeL3Integrity(
        bf=bf, sot=ifaces, node=f"{task.host.name}", properties="Declared_Names"
    )

    data, statistics = dev.call_method_by_name(func_name, **kwargs)

    return Result(host=task.host, result=dict(data=data, statistics=statistics))


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
