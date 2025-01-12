from re import findall
from copy import deepcopy

import ipaddress


# TODO : NEED TO ADD FUNCTIONALITY


def check_ip(ip1: str, ip2: str) -> bool:
    """
    Compare two IPv4 addresses or ranges for equality.

    Args:
        ip1: First IPv4 address or range.
        ip2: Second IPv4 address or range.

    Returns:
        bool: True if the IP addresses or ranges are equal, False otherwise.
    """
    if ip1 == ip2:
        return True

    #  range in rules but not in normal
    if "-" in ip1:
        ip1_upper, ip1_lower = ip1.split("-")
        return ip1_upper > ip2 > ip1_lower

    return False


if __name__ == "__main__":
    pass