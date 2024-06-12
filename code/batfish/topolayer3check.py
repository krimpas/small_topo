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


ifaces_list = {
    "r1": ["GigabitEthernet2", "GigabitEthernet4", "Loopback0"],
    "r2": ["GigabitEthernet2", "GigabitEthernet3", "GigabitEthernet4", "Loopback0"],
    "r3": ["GigabitEthernet2", "GigabitEthernet3", "Loopback0"],
    "r4": ["GigabitEthernet0/1", "GigabitEthernet3", "Loopback0"],
    "r5": ["GigabitEthernet0/1", "GigabitEthernet0/2", "Loopback0", "Loopback5"],
}


ifaces = {
    "r1": {
        "interfaces": [
            {
                "description": "towards OSPF area 0",
                "enabled": True,
                "ipv4": "10.0.0.11",
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
