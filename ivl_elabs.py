from .ivl_enums import IvlElabType, IvlDataDirection


class IvlElab:
    """
    Represents an IVerilog elaboration. These are generated from the
        "Elaborated Nodes" section of the netlist file.

    This is never created directly, but is instead used as a superclass of
        IvlElabPosedge, IvlElabNetPartSelect, and IvlElabLogic.
    """
    def __init__(self, xtype):
        self.xtype = xtype

    def __repr__(self):
        return '<IvlElab: %s>' % self.xtype.name


class IvlElabPosedge(IvlElab):
    """
    Represents an IVerilog posedge elaboration. These are generated when code
        events are associated with nets.
    """
    def __init__(self, net_in):
        IvlElab.__init__(self, IvlElabType.posedge)
        self.net_in = net_in

    def __repr__(self):
        pre = super().__repr__()
        head = pre[:-1]
        output = head
        output += ': event on %s' % self.net_in.name
        output += '>'
        return output


class IvlElabNetPartSelect(IvlElab):
    """
    Represents an IVerilog NetPartSelect elaboration. These are generated when
        one section of a port is connected to another complete port: for
        example, if one bit of a three-bit port is connected to a one-bit port.

    This often coincides with the generation of local nets. To connect one
        partial port to another partial port, IVerilog generates smaller
        intermediary nets the size of the partial ports.
    """
    def __init__(self, net_in, net_out, large_net, bit_pos, pin_count):
        IvlElab.__init__(self, IvlElabType.net_part_select)
        self.net_in = net_in
        self.net_out = net_out
        self.large_net = large_net
        self.bit_pos = bit_pos
        self.pin_count = pin_count

    def __repr__(self):
        last_pin = self.bit_pos + self.pin_count - 1
        bit_pos_count = '[%s:%s]' % (self.bit_pos, last_pin)
        pre = super().__repr__()
        head = pre[:-1]
        output = head
        output += ': %s' % self.net_in.name
        if self.large_net is IvlDataDirection.input:
            output += bit_pos_count
        output += ' -> %s' % self.net_out.name
        if self.large_net is IvlDataDirection.output:
            output += bit_pos_count
        output += '>'
        return output


class IvlElabLogic(IvlElab):
    """
    Represents an IVerilog logic elaboration. These are created when logic
        primitives are used in a Verilog module.
    """
    def __init__(self, logic_type, nets_in, net_out):
        IvlElab.__init__(self, IvlElabType.logic)
        self.logic_type = logic_type
        self.nets_in = nets_in
        self.net_out = net_out

    def __repr__(self):
        pre = super().__repr__()
        head = pre[:-1]
        output = head + ': '
        output += '%s: ' % self.logic_type
        output += '%s -> ' % ', '.join([n.name for n in self.nets_in])
        output += '%s>' % self.net_out.name
        return output
