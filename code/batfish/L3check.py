from L3_info import L3InterfaceInfo
from bfish_L3iface_props import BFISH_L3IFACE_PROPS, L3IFACE_TYPES


def main():

    iface = L3InterfaceInfo(
        node="r1", properties=BFISH_L3IFACE_PROPS.select_properties()
    )
    print("\n")
    # variable=f"Checking Gigabit Ethernet subnets"
    # print(f"|< {variable:-^78} >|")
    print(iface.check_L3_interface(anet="10.0.0.0/29", ifacetype="Gig"))
    print("\n")
    # variable2= f"Checking Loopback subnets"
    # print(f"|< {variable2:-^78} >|")
    print(iface.check_L3_interface(anet="172.16.0.0/24", ifacetype="Loop"))
    print("\n")


if __name__ == "__main__":
    main()
