from L3_info import L3InterfaceInfo
from bfish_L3iface_props import BFISH_L3IFACE_PROPS


def main():

    iface = L3InterfaceInfo(
        node="r2", properties=BFISH_L3IFACE_PROPS.select_properties()
    )

    result = iface.check_L3_interface(anet="10.0.0.0/28", ifacetype="Gig")
    for i in range(result.shape[0]):
        print(result.iloc[i])
    print("\n")

    result = iface.check_L3_interface(anet="172.16.0.0/24", ifacetype="Loop")
    for i in range(result.shape[0]):
        print(result.iloc[i])
    print("\n")


if __name__ == "__main__":
    main()
