from .ivl_structures import IvlNet

import re


class IvlNetManager:
    def __init__(self):
        self.nets = {}

    def get_net(self, net_id):
        return self.nets[net_id]

    def get_or_make_net(self, net_id, net_name):
        if net_id not in self.nets:
            self.nets[net_id] = IvlNet(net_id, net_name)
        return self.nets[net_id]

    def _add_member_to_net(self, net_id, net_name, member):
        net = self.get_or_make_net(net_id, net_name)
        net.add_member(member)
        return net

    def add_port_to_net(self, net_id, net_name, port):
        net = self._add_member_to_net(net_id, net_name, port)
        port.set_net(net)
        return net


def leading_spaces(line):
    return len(line) - len(line.lstrip(' '))


def group_lines(lines):
    groups = []
    group = []
    if lines:
        for line in lines:
            if leading_spaces(line) == 0:
                if group:
                    groups.append(group)
                    group = []
            group.append(line)
        if group:
            groups.append(group)
    return groups


is_local_regex = '\(local\)'
is_local_finder = re.compile(is_local_regex)
