import os
import logging
from L3_info import L3InterfaceInfo
from bfish_L3iface_props import BFISH_L3IFACE_PROPS
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from dotenv import load_dotenv

load_dotenv()


def exec_task(atask: Task) -> Result:
    #
    # Create the L3info object
    device = L3InterfaceInfo(
        node=f"{atask.host.name}", properties=BFISH_L3IFACE_PROPS.select_properties()
    )

    res = device.check_L3_interface(anet="10.0.0.0/28", ifacetype="Gig")

    return Result(host=atask.host, result=res)


def main():
    # Initialize Nornir
    nr = InitNornir(config_file=os.environ.get("NORNIR_CONFIG_FILE"))

    # Run the validation task on all filtered hosts
    result = nr.run(
        name="L3 GigaBit Batfish checks",
        task=exec_task,
        severity_level=logging.INFO,
    )

    # Print the results
    print_result(result.result)


if __name__ == "__main__":
    main()
