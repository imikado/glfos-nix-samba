class SambaHost:
    """A Samba server discovered on the local network."""

    name: str
    hostname: str
    address: str

    def __init__(self, name: str, hostname: str, address: str):
        self.name = name
        self.hostname = hostname
        self.address = address

    def __eq__(self, other):
        return isinstance(other, SambaHost) and (self.name, self.hostname, self.address) == (other.name, other.hostname, other.address)

    def __repr__(self):
        return f'SambaHost({self.name!r}, {self.hostname!r}, {self.address!r})'
