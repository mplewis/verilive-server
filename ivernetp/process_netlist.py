from .parsers import parse_modules_and_elabs
from .ivl_enums import IvlElabType, IvlPortType, IvlDataDirection
from .utils import IvlNetManager

import json


def netlist_to_json(raw_netlist):
    net_manager = IvlNetManager()
    modules, elabs = parse_modules_and_elabs(raw_netlist, net_manager)

    local_nets = set()
    for module in modules:
        for port in module.ports:
            if port.is_local:
                local_nets.add(port.net)

    unmatched_local_ins = {}
    unmatched_local_outs = {}

    nps_elabs = [e for e in elabs if e.xtype is IvlElabType.net_part_select]
    for e in nps_elabs:
        if e.net_in in local_nets:
            unmatched_local_ins[e.net_in] = e
        elif e.net_out in local_nets:
            unmatched_local_outs[e.net_out] = e

    logic_elabs = [e for e in elabs if e.xtype is IvlElabType.logic]
    for e in logic_elabs:
        if e.net_out in unmatched_local_ins:
            match = unmatched_local_ins[e.net_out]
            new_out = match.net_out
            e.net_out = new_out
        for pos, net in enumerate(e.nets_in):
            if net in unmatched_local_outs:
                match = unmatched_local_outs[net]
                new_in = match.net_in
                e.nets_in[pos] = new_in

    nodes = []
    edges = []

    for module in modules:
        full_name = module.name
        short_name = None
        parent = None
        try:
            parent, short_name = module.name.rsplit('.', 1)
        except ValueError:
            short_name = full_name
        nodes.append({'id': full_name, 'label': '%s\\n<%s>' %
                     (short_name, module.xtype)})
        if parent:
            edges.append({'from': parent, 'to': full_name})

    output = {'nodes': nodes, 'edges': edges}

    nodes = []
    edges = []

    all_nets = net_manager.nets.values()
    nets = [n for n in all_nets if len(n.members) > 1]

    for module in modules:
        full_name = module.name
        short_name = None
        parent = None
        try:
            parent, short_name = module.name.rsplit('.', 1)
        except ValueError:
            short_name = full_name
        nodes.append({'id': full_name, 'label': '%s\\n<%s>' %
                     (short_name, module.xtype)})

    for net in nets:
        inputs = []
        outputs = []
        for member in net.members:
            direction = None
            if member.direction:
                direction = member.direction
            elif member.xtype is IvlPortType.wire:
                direction = IvlDataDirection.input
            elif member.xtype is IvlPortType.reg:
                direction = IvlDataDirection.output

            if direction is IvlDataDirection.input:
                inputs.append(member)
            elif direction is IvlDataDirection.output:
                outputs.append(member)

        for i in inputs:
            for o in outputs:
                label = '%s → %s' % (o.name, i.name)
                if i.width > o.width:
                    width = i.width
                else:
                    width = o.width
                i_id = i.parent_module.name
                o_id = o.parent_module.name
                edges.append({'from': o_id, 'to': i_id, 'width': width,
                              'label': label})

    output = {'nodes': nodes, 'edges': edges}
    return json.dumps(output)


if __name__ == '__main__':
    with open('test.netlist') as f:
        raw_netlist = f.read()
    print(netlist_to_json(raw_netlist))
