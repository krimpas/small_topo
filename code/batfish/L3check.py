import os
import logging
from L3_info import L3InterfaceInfo
from bfish_L3iface_props import BFISH_L3IFACE_PROPS
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from dotenv import load_dotenv
from bfish_init import bfish_init
from pybatfish.client.session import Session
from L3check2 import dfprint

load_dotenv()


def exec_task(task: Task, bf: Session, anet: str = "", ifacetype: str = "") -> Result:
    #
    # Create the L3info object
    device = L3InterfaceInfo(
        bf=bf,
        node=f"{task.host.name}",
        properties=BFISH_L3IFACE_PROPS.select_properties(),
    )

    res = device.check_L3_interface(anet=anet, ifacetype=ifacetype)
    dfprint(
        df=res,
        props=["#"] + [c for c in res.columns],
        title="Checking L3 interfaces",
    )
    )
    return Result(host=task.host, result=dict(is_valid=True, ifacelist=res))


def main():
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))
    bf_session = bfish_init()

    # Run the validation task on all filtered hosts
    result = nr.run(
        name="L3 Loopback Batfish checks",
        task=exec_task,
        bf=bf_session,
        anet="172.16.0.0/16",
        ifacetype="Loop",
        severity_level=logging.INFO,
    )

    # Print the results
    # print_result(result)

    result = nr.run(
        name="L3 GigaBit Batfish checks",
        task=exec_task,
        bf=bf_session,
        anet="10.0.0.0/8",
        ifacetype="Gig",
        severity_level=logging.INFO,
    )

    # Print the results
    print_result(result)


if __name__ == "__main__":
    main()
