from .ivl_enums import IvlElabType, IvlPortType, IvlDataDirection
from .parsers import parse_modules_and_elabs
from .utils import IvlNetManager

import pytest
import sure  # noqa


@pytest.yield_fixture
def read_netlist():
    """
    Read a netlist and parse it into modules and elabs.
    Create a new net manager as well.
    Return all three as a tuple.
    """
    with open('test.netlist') as f:
        test_netlist = f.read()
    net_manager = IvlNetManager()
    modules, elabs = parse_modules_and_elabs(test_netlist, net_manager)
    yield (modules, elabs, net_manager)


def test_counts(read_netlist):
    """Make sure the right number of things are produced."""
    modules, elabs, net_manager = read_netlist
    len(modules).should.be.equal(6)
    len(elabs).should.be.equal(27)


def test_types(read_netlist):
    """Make sure the right types appear."""
    modules, elabs, net_manager = read_netlist
    len([m for m in modules if m.xtype == 'tff']).should.be.equal(3)
    net_part_selects = [e for e in elabs if
                        e.xtype is IvlElabType.net_part_select]
    len(net_part_selects).should.be.equal(18)
    posedges = [e for e in elabs if e.xtype is IvlElabType.posedge]
    len(posedges).should.be.equal(3)
    logics = [e for e in elabs if e.xtype is IvlElabType.logic]
    len(logics).should.be.equal(6)


def test_ports(read_netlist):
    """Make sure ports are generated properly."""
    modules, elabs, net_manager = read_netlist
    tb = [m for m in modules if m.xtype == 'bargraph_testbench'][0]
    len(tb.ports).should.be.equal(3)
    regs = [p for p in tb.ports if p.xtype is IvlPortType.reg]
    len(regs).should.be.equal(1)
    wires = [p for p in tb.ports if p.xtype is IvlPortType.wire]
    len(wires).should.be.equal(2)


def test_local_ports(read_netlist):
    """Check for generation of local wire-type ports."""
    modules, elabs, net_manager = read_netlist
    bg = [m for m in modules if m.xtype == 'bargraph3'][0]
    local_ports = [p for p in bg.ports if p.is_local]
    len(local_ports).should.be.equal(15)


def test_port_types(read_netlist):
    """Check for proper port typing."""
    modules, elabs, net_manager = read_netlist
    tff = [m for m in modules if m.xtype == 'tff'][0]
    inputs = [p for p in tff.ports if
              p.direction is IvlDataDirection.input]
    len(inputs).should.be.equal(2)
    outputs = [p for p in tff.ports if
               p.direction is IvlDataDirection.output]
    len(outputs).should.be.equal(2)


def test_nets(read_netlist):
    """Check for proper net generation."""
    modules, elabs, net_manager = read_netlist
    to_bg = net_manager.get_net('0x7fbd08d0a950')
    len(to_bg.members).should.be.equal(3)
