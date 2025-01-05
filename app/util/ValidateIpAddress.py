def ValidateIpAddress(ip_address: str) -> bool:
        parts = ip_address.split('.')
        if len(parts) != 4:
            return False
        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)
