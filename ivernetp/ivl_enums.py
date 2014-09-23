from enum import Enum


class IvlPortType(Enum):
    """
    Represents the type of an IvlPort.
    reg and wire are standard types declared in code.
    event is a type created by IVerilog when modules are linked to code events.
    """
    reg = 1
    wire = 2
    event = 3


class IvlDataDirection(Enum):
    """
    Represents the direction data flows to/from a part.
    Used by both IvlNet and IvlPort.
    """
    input = 1
    output = 2


class IvlElabType(Enum):
    """
    Represents the type of an IvlElab.
    """
    net_part_select = 1
    logic = 2
    posedge = 3
