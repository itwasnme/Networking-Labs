import sys
import os
import os.path
# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../utils/'))
import p4runtime_lib.bmv2
import p4runtime_lib.helper
import grpc
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
from p4runtime_lib.convert import decodeNum

def install_table_entry(the_switch, dst_mac_addresss, egress_spec):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.mac_dst_lpm",
        match_fields={
            "hdr.ethernet.dstAddr": (dst_mac_address, 48)
        },
        action_name="MyIngress.to_egresss_spec",
        action_params={
            "spec": tunnel_id,
        })
    the_switch.WriteTableEntry(table_entry)

def read_table_entries(p4info_helper, sw):
    """
    Reads the table entries from all tables on the switch.

    :param p4info_helper: the P4Info helper
    :param sw: the switch connection
    """
    print('\n----- Reading tables rules for %s -----' % sw.name)
    for response in sw.ReadTableEntries():
        for entity in response.entities:
            entry = entity.table_entry
            # TODO For extra credit, you can use the p4info_helper to translate
            #      the IDs in the entry to names
            print(entry)
            print('-----')


def print_counter(p4info_helper, sw, counter_name, index):
    """
    Reads the specified counter at the specified index from the switch. In our
    program, the index is the tunnel ID. If the index is 0, it will return all
    values from the counter.

    :param p4info_helper: the P4Info helper
    :param sw:  the switch connection
    :param counter_name: the name of the counter from the P4 program
    :param index: the counter index (in our case, the tunnel ID)
    """
    for response in sw.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
        for entity in response.entities:
            counter = entity.counter_entry
            print("%s %s %d: %d packets (%d bytes)" % (
                sw.name, counter_name, index,
                counter.data.packet_count, counter.data.byte_count
            ))

def write_table_entry(p4info_helper, switch, table_name, match_fields, action_name, action_params,
                      modify=None):
    table_entry = p4info_helper.buildTableEntry(
        table_name=table_name,
        match_fields=match_fields,
        action_name=action_name,
        action_params=action_params,
    )
    switch.WriteTableEntry(table_entry, modify=modify)

def delete_table_entry(p4info_helper, switch, table_name, match_fields, action_name, action_params):
        write_table_entry(p4info_helper, switch, table_name, match_fields, action_name, action_params, delte=True)

def write_or_overwrite_table_entry(p4info_helper, switch, table_name, match_fields, action_name, action_params):
    try:
        write_table_entry(p4info_helper, switch, table_name, match_fields, action_name, action_params)
    except grpc.RpcError as e:
        write_table_entry(p4info_helper, switch, table_name, match_fields, action_name, action_params, modify=True)


def decode_packet_in_metadata(p4info_helper, switch, the_metadata):
    schema = p4info_helper.get('controller_packet_metadata', name='packet_in')
    fields_by_id = {}
    for field_info in schema.metadata:
        fields_by_id[field_info.id] = field_info

    result = {}
    for field in the_metadata:
        field_info = fields_by_id[field.metadata_id]
        expect_bytes = field_info.bitwidth // 8
        cur_value = bytearray(expect_bytes)
        cur_value[0:len(field.value)] = field.value
        result[field_info.name] = bytes(cur_value)
    return result
