from .ivl_structures import IvlModule, IvlPort
from .ivl_elabs import IvlElabNetPartSelect, IvlElabPosedge, IvlElabLogic
from .ivl_enums import IvlElabType, IvlPortType, IvlDataDirection
from .utils import leading_spaces, is_local_finder, group_lines

import re

# Used to lookup enum types from strings
ELAB_TYPE_LOOKUP = {
    'NetPartSelect': IvlElabType.net_part_select,
    'posedge': IvlElabType.posedge,
    'logic': IvlElabType.logic
}


def parse_netlist_to_sections(raw_netlist):
    """
    Take raw text from a netlist file and turn it into lists of lines grouped
    by section.

    Sections look like this:
        SCOPES:
        ELABORATED NODES:
        ...etc.

    Returns a dict.
    Keys are the name of the section.
    Values are an array of lines that make up that section.
    """
    # This regex matches lines that start with a caps letter, contain caps and
    # spaces, and are followed by a colon, then any characters
    section_regex = '[A-Z][A-Z ]*:.*'
    section_finder = re.compile(section_regex)
    sections = {}
    title = None
    section = []
    for line in raw_netlist.split('\n'):
        if section_finder.match(line):
            if not section:
                section = None
            if title:
                sections[title] = section
            section = []
            title, data = line.split(':')
            if data:
                section = data.strip()
        else:
            section.append(line)
    if title:
        sections[title] = section
    return sections


def parse_module_lines(lines, net_manager):
    """
    Parse lines that make up a module. Add the module to the proper nets using
    the specified NetManager.

    Returns an IvlModule object.
    """
    module_meta = lines[0]
    module_data = lines[1:]
    name, supertype, module_type_raw, inst_type = module_meta.split(' ')
    module_type = module_type_raw.lstrip('<').rstrip('>')
    ports = parse_module_data(module_data, net_manager)
    module = IvlModule(name, module_type, ports)
    for port in ports:
        port.parent_module = module
    return module


def parse_module_data(lines, net_manager):
    """
    Parse the module data (not the first line, which is metadata).

    Returns a list of IvlPort objects created from the module.
    """
    ports = []
    port = None
    for line in lines:
        # Port declarations have four leading spaces
        if leading_spaces(line) == 4:
            if port:
                ports.append(port)
                port = None
            line = line.lstrip(' ')

            # reg or wire lines
            if line.startswith('reg') or line.startswith('wire'):
                is_local = is_local_finder.search(line)

                # Line starts with either 'reg' or 'wire'
                if line.startswith('reg'):
                    xtype = IvlPortType.reg
                else:
                    xtype = IvlPortType.wire

                # reg: <name>[0:0 count=1]
                # wire: <name>[0:0 count=1]
                name = line.split(': ')[1].split('[')[0]

                # wire: in[0:0 count=1] logic <direction_raw> (eref=0, lref=0)
                direction_raw = (line
                                 .split('logic')[1]
                                 .split('(eref')[0]
                                 .strip(' '))

                # Convert direction_raw to an IvlDataDirection
                try:
                    direction = IvlDataDirection[direction_raw]
                except KeyError:
                    direction = None

                # vector_width=<width>
                width = int(line
                            .split('vector_width=')[1]
                            .split(' pin_count=')[0])

                port = IvlPort(name, xtype, width=width, direction=direction,
                               is_local=is_local)

            # event lines
            elif line.startswith('event'):
                xtype = IvlPortType.event

                # event <name>;
                name = line.split('event ')[1].split(';')[0]

                # event _s0; ... // <snippet>
                snippet = line.split('// ')[1]

                port = IvlPort(name, xtype, code_snippet=snippet)

        # Port data lines have eight leading spaces
        elif leading_spaces(line) == 8:
            if port:
                net_id, net_name = line.split(': ')[1].split(' ')
                net_manager.add_port_to_net(net_id, net_name, port)

    if port:
        ports.append(port)
    return ports


def parse_elab_bundle_lines(lines, net_manager):
    """
    Parses lines from an elab into a Logic, Posedge, or NetPartSelect IvlElab
    object.

    Returns the new IvlElab object.
    """
    # posedge -> ...
    # NetPartSelect(PV): ...
    # logic: ...
    xtype_raw = lines[0].split(' -> ')[0].split('(')[0].split(':')[0]
    xtype = ELAB_TYPE_LOOKUP[xtype_raw]
    info_split = lines[0].split(' ')

    if xtype is IvlElabType.net_part_select:
        # NetPartSelect(<io_size_flag>): <name> #(.,.,.) \
        # off=<offset> wid=<width>

        offset = int(info_split[3][4:])
        width = int(info_split[4][4:])

        # PV vs VP indicates which port is larger, the first or second
        io_size_flag = lines[0].split('(')[1].split(')')[0]
        if io_size_flag == 'PV':
            large_net = IvlDataDirection.output
        elif io_size_flag == 'VP':
            large_net = IvlDataDirection.input
        else:
            raise ValueError('Invalid IO size flag: %s' % io_size_flag)

    elif xtype is IvlElabType.logic:
        # logic: <logic_type> ...
        logic_type = info_split[1]

    input_nets = []
    output_nets = []
    for line in lines[1:]:
        # Net lines have four leading spaces. Example line:
        # 0 pin0 I (strong0 strong1): 0x7fbd08d0a630 bargraph_testbench.b._s0
        line_split = line.split(' ')
        data_dir = line_split[6]
        net_id = line_split[9]
        net_name = line_split[10]
        net = net_manager.get_or_make_net(net_id, net_name)
        if data_dir == 'I':
            input_nets.append(net)
        elif data_dir == 'O':
            output_nets.append(net)
        else:
            raise ValueError('Invalid net data direction: %s' % data_dir)

    if xtype is IvlElabType.net_part_select:
        elab = IvlElabNetPartSelect(input_nets[0], output_nets[0], large_net,
                                    offset, width)

    elif xtype is IvlElabType.posedge:
        elab = IvlElabPosedge(input_nets[0])

    elif xtype is IvlElabType.logic:
        elab = IvlElabLogic(logic_type, input_nets, output_nets[0])

    else:
        raise ValueError('Invalid elab xtype: %s' % xtype)

    return elab


def parse_modules_and_elabs(raw_netlist, net_manager):
    """
    Parses a raw netlist into its IvlModule and IvlElab objects.

    Returns a tuple: (modules, elabs)
    modules is a list of IvlModule objects.
    elabs is a list of IvlElab objects.
    """
    sections = parse_netlist_to_sections(raw_netlist)
    modules_lines = group_lines(sections['SCOPES'])
    elab_bundles_lines = group_lines(sections['ELABORATED NODES'])

    modules = [parse_module_lines(lines, net_manager)
               for lines in modules_lines]
    elabs = [parse_elab_bundle_lines(lines, net_manager)
             for lines in elab_bundles_lines]
    return modules, elabs
