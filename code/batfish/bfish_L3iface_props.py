import enum

_COMMA = ","

@enum.unique
class BFISH_L3IFACE_PROPS(str, enum.Enum):
    """
    Enum for Cisco unique Interface Types as string constants
    """

    ACTIVE = "Active"
    ADMIN_UP = "Admin_Up"
    ALL_PREFIXES = "All_Prefixes"
    BANDWIDTH = "Bandwidth"
    DESCRIPTION = "Description"
    MTU = "MTU"
    PRIMARY_ADDRESS = "Primary_Address"
    PRIMARY_NETWORK = "Primary_Network"
    SPEED = "Speed"

    @staticmethod
    def select_properties():
        """All selected interface attibutes as a comma seperated string.
        Used as properties arg by batfish bfq.interfaceProperties()
        """
        return str(_COMMA.join(BFISH_L3IFACE_PROPS))


@enum.unique
class L3IFACE_TYPES(str, enum.Enum):
    """
    Enum for Cisco unique Interface Types as string constants
    """

    LOOP = "Loopback"
    FAST = "FastEthernet"
    GIGBIT = "GigabitEthernet"
    TENGIG = "TenGigabitEthernet"
    TUNNEL = "Tunnel"
