import argparse
import json
import abc
from enum import Enum
from tatsu import parse as tatsu_parse
from tatsu import compile as tatsu_compile
from tatsu import to_python_sourcecode
from pathlib import Path
from typing import Dict, List, Tuple

class DbcAttributeType(abc.ABC):
    def __init__(self):
        pass
    def is_integer(self) -> bool:
        return False
    def is_hex(self) -> bool:
        return False
    def is_enum(self) -> bool:
        return False
    def is_float(self) -> bool:
        return False
    def is_string(self) -> bool:
        return False

class DbcIntegerType(DbcAttributeType):
    def __init__(self, min: int, max: int):
        super().__init__()
        self.min = min
        self.max = max
    def is_integer(self) -> bool:
        return True

class DbcFloatType(DbcAttributeType):
    def __init__(self, min: float, max: float):
        super().__init__()
        self.min = min
        self.max = max
    def is_float(self) -> bool:
        return True

class DbcHexType(DbcAttributeType):
    def __init__(self, min: int, max: int):
        super().__init__()
        self.min = min
        self.max = max
    def is_hex(self) -> bool:
        return True

class DbcEnumType(DbcAttributeType):
    def __init__(self):
        super().__init__()
        self.labels: List[str] = list()
    def add_label(self, label: str):
        self.labels.append(label)
    def is_enum(self) -> bool:
        return True

class DbcStringType(DbcAttributeType):
    def __init__(self):
        super().__init__()
    def is_string(self) -> bool:
        return True

class DbcAttributeObjectType(Enum):
    GLOBAL=0
    NODE=1
    MESSAGE=2
    SIGNAL=3
    ENVIRONMENT_VARIABLE=4
    NODE_MESSAGE=5
    NODE_SIGNAL=6
    NODE_ENVIRONMENT_VARIABLE=7

class DbcAttribute:
    def __init__(self, name: str, value_type: DbcAttributeType, object_type: DbcAttributeObjectType):
        self.name = name
        self.value_type = value_type
        self.object_type = object_type
        self.default: DbcAttributeValue = None
    def __repr__(self) -> str:
        return f"DbcAttribute:{self.name}"
    def __str__(self) -> str:
        return f"DbcAttribute:{self.name}"

class DbcAttributeValue:
    def __init__(self, attribute: DbcAttribute, value):
        self.name = attribute.name
        self.attribute = attribute
        self.value = value
    def __repr__(self) -> str:
        return f"DbcAttributeValue:{self.name}={self.value}"
    def __str__(self) -> str:
        return f"DbcAttributeValue:{self.name}={self.value}"

class DbcNode:
    def __init__(self, name: str):
        self.name = name
        self.description = "N/A"
        self.attributes: Dict[str, DbcAttributeValue] = dict()
    def add_attribute(self, attr: DbcAttributeValue):
        if attr.name in self.attributes:
            raise RuntimeError(f"Attribute {attr.name} already in signal {self.name}")
        self.attributes[attr.name] = attr
    def has_attribute(self, name: str) -> bool:
        return name in self.attributes
    def get_attribute(self, name: str) -> DbcAttributeValue:
        attr = self.attributes[name]
        return attr
    def __repr__(self) -> str:
        return f"DbcNode:{self.name}"
    def __str__(self) -> str:
        return f"DbcNode:{self.name}"

class DbcSignalValueType(Enum):
    UNSIGNED=0
    SIGNED=1
    FLOAT32=2
    FLOAT64=3

class DbcSignalByteOrder(Enum):
    LITTLE_ENDIAN=0
    BIG_ENDIAN=1

class DbcSignal:
    def __init__(self, signal_name: str, start_bit: int, signal_size: int, byte_order: DbcSignalByteOrder, value_type: DbcSignalValueType, factor: float, offset: float, minimum: float, maximum: float, unit: str):
        self.name = signal_name
        self.start_bit = start_bit
        self.size = signal_size
        self.byte_order = byte_order
        self.value_type = value_type
        self.factor = factor
        self.offset = offset
        self.minimum = minimum
        self.maximum = maximum
        self.unit = unit
        self.attributes: Dict[str, DbcAttributeValue] = dict()
        self.description: str = "N/A"
        self.value_descriptions: List[Tuple[float, str]] = list()
    def add_attribute(self, attr: DbcAttributeValue):
        if attr.name in self.attributes:
            raise RuntimeError(f"Attribute {attr.name} already in signal {self.name}")
        self.attributes[attr.name] = attr
    def has_attribute(self, name: str) -> bool:
        return name in self.attributes
    def get_attribute(self, name: str) -> DbcAttributeValue:
        attr = self.attributes[name]
        return attr
    def add_value_description(self, val: float, label: str):
        self.value_descriptions.append((val, label))
    def __repr__(self) -> str:
        return f"DbcSignal:{self.name}"
    def __str__(self) -> str:
        return f"DbcSignal:{self.name}"

class DbcSignalGroup:
    def __init__(self, name: str, repetitions: int):
        self.name = name
        self.repetitions = repetitions
        self.signals: List[DbcSignal] = list()
    def _add_signal(self, signal: DbcSignal):
        self.signals.append(signal)
    def __repr__(self) -> str:
        return f"DbcSignalGroup:{self.name}"
    def __str__(self) -> str:
        return f"DbcSignalGroup:{self.name}"

class DbcMessage:
    def __init__(self, message_id: int, message_name: str, message_size: int, transmitter: str):
        self.id = message_id
        self.name = message_name
        self.size = message_size
        self.description = "N/A"
        self.transmitter = transmitter
        self.signals_by_name: Dict[str, DbcSignal] = dict()
        self.attributes: Dict[str, DbcAttributeValue] = dict()
        self.signal_groups: List[DbcSignalGroup] = list()
    def add_attribute(self, attr: DbcAttributeValue):
        if attr.name in self.attributes:
            raise RuntimeError(f"Attribute {attr.name} already in message {self.name}")
        self.attributes[attr.name] = attr
    def has_attribute(self, name: str) -> bool:
        return name in self.attributes
    def get_attribute(self, name: str) -> DbcAttributeValue:
        attr = self.attributes[name]
        return attr
    def _add_signal(self, signal: DbcSignal):
        if signal.name in self.signals_by_name:
            raise RuntimeError(f"Signal {signal.name} already in message {self.name}")
        self.signals_by_name[signal.name] = signal
    def _add_signal_group(self, sg: DbcSignalGroup):
        self.signal_groups.append(sg)
    def get_signals(self) -> List[DbcSignal]:
        return list(self.signals_by_name.values())
    def get_signal(self, name: str) -> DbcSignal:
        return self.signals_by_name[name]
    def __repr__(self) -> str:
        return f"DbcMessage:{self.name}"
    def __str__(self) -> str:
        return f"DbcMessage:{self.name}"

class DbcEnvironmentVariableType(Enum):
    INTEGER=0
    FLOAT=1
    STRING=2
    DATA=3

class DbcEnvironmentVariableAccessType(Enum):
    UNRESTRICTED=0
    READ=1
    WRITE=2
    READ_WRITE=3

class DbcEnvironmentVariable:
    def __init__(self, name: str, type: DbcEnvironmentVariableType, data_size: int, min: float, max: float, unit: str, init_value: float, id: int, access_type: DbcEnvironmentVariableAccessType):
        self.name = name
        self.type = type
        self.minimum = min
        self.maximum = max
        self.unit = unit
        self.init_value = init_value
        self.id = id
        self.access_type = access_type
        self.access_nodes: List[DbcNode] = list()
        self.description: str = "N/A"
        self.attributes: Dict[str, DbcAttributeValue] = dict()
        self.value_descriptions: List[Tuple[float, str]] = list()
        self.data_size: int = 0
    def _add_access_node(self, node: DbcNode):
        self.access_nodes.append(node)
    def add_attribute(self, attr: DbcAttributeValue):
        if attr.name in self.attributes:
            raise RuntimeError(f"Attribute {attr.name} already in evar {self.name}")
        self.attributes[attr.name] = attr
    def has_attribute(self, name: str) -> bool:
        return name in self.attributes
    def get_attribute(self, name: str) -> DbcAttributeValue:
        attr = self.attributes[name]
        return attr
    def add_value_description(self, val: float, label: str):
        self.value_descriptions.append((val, label))
    def __repr__(self) -> str:
        return f"DbcEnvironmentVariable:{self.name}"
    def __str__(self) -> str:
        return f"DbcEnvironmentVariable:{self.name}"

class DbcValueTable:
    def __init__(self, name: str):
        self.name = name
        self.values: Dict[str, float] = dict()
    def _add_value(self, value: float, label: str):
        if label in self.values:
            raise RuntimeError(f"Label {label} already in value table")
        self.values[label] = value

class DbcFile:
    def __init__(self):
        self.version = "N/A"
        self.nodes_by_name: Dict[str, DbcNode] = dict()
        self.messages_by_id: Dict[int, DbcMessage] = dict()
        self.environment_variables_by_name: Dict[str, DbcEnvironmentVariable] = dict()
        self.attribute_definitions: Dict[str, DbcAttribute] = dict()
        self.attribute_values: Dict[str, DbcAttributeValue] = dict()
        self.value_tables_by_name: Dict[str, DbcValueTable] = dict()
    def _add_message(self, message: DbcMessage):
        if message.id in self.messages_by_id:
            raise RuntimeError(f"Message {message.id} already in Dbc")
        self.messages_by_id[message.id] = message
    def _add_value_table(self, vtable: DbcValueTable):
        if vtable.name in self.value_tables_by_name:
            raise RuntimeError(f"Value table {vtable.name} already in Dbc")
        self.value_tables_by_name[vtable.name] = vtable
    def _add_environment_variable(self, ev: DbcEnvironmentVariable):
        if ev.name in self.environment_variables_by_name:
            raise RuntimeError(f"Message {ev.name} already in Dbc")
        self.environment_variables_by_name[ev.name] = ev
    def _add_node(self, node: DbcNode):
        if node.name in self.nodes_by_name:
            raise RuntimeError(f"Node {node.name} already in Dbc")
        self.nodes_by_name[node.name] = node
    def _add_attribute_definition(self, attr: DbcAttribute):
        if attr.name in self.attribute_definitions:
            raise RuntimeError(f"Attribute {attr.name} already in Dbc")
        self.attribute_definitions[attr.name] = attr
    def has_attribute_definition(self, name: str) -> bool:
        return name in self.attribute_definitions
    def get_attribute_definition(self, name: str) -> DbcAttribute:
        attr = self.attribute_definitions[name]
        return attr
    def add_attribute_value(self, attr: DbcAttributeValue):
        if attr.name in self.attribute_values:
            raise RuntimeError(f"Attribute {attr.name} already in Dbc")
        self.attribute_values[attr.name] = attr
    def has_attribute_value(self, name: str) -> bool:
        return name in self.attribute_values
    def get_attribute_value(self, name: str) -> DbcAttributeValue:
        attr = self.attribute_values[name]
        return attr
    def has_node(self, name: str) -> bool:
        return name in self.nodes_by_name
    def get_node(self, name: str) -> DbcNode:
        return self.nodes_by_name[name]
    def has_message(self, id: int) -> bool:
        return id in self.messages_by_id
    def get_message(self, id: int) -> DbcMessage:
        return self.messages_by_id[id]
    def has_value_table(self, name: str) -> bool:
        return name in self.value_tables_by_name
    def get_value_table(self, name: str) -> DbcValueTable:
        return self.value_tables_by_name[name]
    def get_environment_variable(self, name: str) -> DbcEnvironmentVariable:
        return self.environment_variables_by_name[name]
    def __repr__(self) -> str:
        return f"DbcFile:{self.version}"
    def __str__(self) -> str:
        return f"DbcFile:{self.version}"

def read_char_string(value: str) -> str:
    if value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    else:
        return value

def read_float_with_default(value: str, default: float) -> float:
    if not value:
        return default
    else:
        return read_float(value)

def read_float(value: str) -> float:
        num_str = join_parsed_number(value)
        return float(num_str)

def read_int(value: str) -> int:
    num_str = join_parsed_number(value)
    return int(num_str)

def read_env_var_type(value: str) -> DbcEnvironmentVariableType:
    if value == "0":
        return DbcEnvironmentVariableType.INTEGER
    elif value == "1":
        return DbcEnvironmentVariableType.FLOAT
    elif value == "2":
        return DbcEnvironmentVariableType.STRING
    else:
        raise RuntimeError(f"Unexpecte evar type {value}")

def read_env_var_access_type(value: str) -> DbcEnvironmentVariableAccessType:
    if value == "DUMMY_NODE_VECTOR0":
        return DbcEnvironmentVariableAccessType.UNRESTRICTED
    elif value == "DUMMY_NODE_VECTOR1":
        return DbcEnvironmentVariableAccessType.READ
    elif value == "DUMMY_NODE_VECTOR2":
        return DbcEnvironmentVariableAccessType.WRITE
    elif value == "DUMMY_NODE_VECTOR3":
        return DbcEnvironmentVariableAccessType.READ_WRITE
    elif value == "DUMMY_NODE_VECTOR8000":
        return DbcEnvironmentVariableAccessType.UNRESTRICTED
    else:
        raise RuntimeError(f"Unexpecte evar access type {value}")

def join_parsed_number(ast) -> str:
    result = ""
    for node in ast:
        if isinstance(node, str):
            result += node
        else:
            node_str = join_parsed_number(node)
            result += node_str
    return result

def read_attribute_value_type(ast) -> DbcAttributeType:
    if len(ast) == 3:
        attr_type = ast[0]
        if attr_type == "INT":
            min = int(ast[1])
            max = int(ast[2])
            return DbcIntegerType(min, max)
        elif attr_type == "HEX":
            min = int(ast[1])
            max = int(ast[2])
            return DbcHexType(min, max)
        elif attr_type == "FLOAT":
            min = float(ast[1])
            max = float(ast[2])
            return DbcFloatType(min, max)
        elif attr_type == "ENUM":
            val1 = DbcEnumType()
            if len(ast) > 1:
                first_label = read_char_string(ast[1])
                val1.add_label(first_label)
                more_labels = ast[2]
                for more_label in more_labels:
                    label = read_char_string(more_label[1])
                    val1.add_label(label)
            return val1
        else:
            raise NotImplementedError(f"TODO")
    elif ast == "STRING":
        return DbcStringType()
    else:
        raise NotImplementedError(f"TODO")

def read_attribute_value(ast, attribute: DbcAttribute) -> DbcAttributeValue:
    value_type = attribute.value_type
    if value_type.is_integer():
        value = int(ast)
        return DbcAttributeValue(attribute, value)
    elif value_type.is_hex():
        value = int(ast)
        return DbcAttributeValue(attribute, value)
    elif value_type.is_float():
        value = float(ast)
        return DbcAttributeValue(attribute, value)
    elif value_type.is_string():
        value = read_char_string(ast)
        return DbcAttributeValue(attribute, value)
    elif value_type.is_enum():
        value = read_char_string(ast)
        return DbcAttributeValue(attribute, value)
    else:
        raise NotImplementedError(f"TODO")

def read_signal_value_type(ast) -> DbcSignalValueType:
    if ast == "+":
        return DbcSignalValueType.UNSIGNED
    elif ast == "-":
        return DbcSignalValueType.SIGNED
    else:
        raise RuntimeError(f"Unexpected signal value type {ast}")

def read_byte_order(ast) -> DbcSignalByteOrder:
    if ast == "0":
        return DbcSignalByteOrder.LITTLE_ENDIAN
    elif ast == "1":
        return DbcSignalByteOrder.BIG_ENDIAN
    else:
        raise RuntimeError(f"Unexpected signal byte_order {ast}")

def read_extended_value_type(ast, sig: DbcSignal) -> DbcSignalValueType:
    if ast == '0':
        return sig.value_type
    elif ast == '1':
        return DbcSignalValueType.FLOAT32
    elif ast == '2':
        return DbcSignalValueType.FLOAT64
    else:
        raise RuntimeError(f"Unexpected extended value type {ast}")

class DbcFactory:
    def __init__(self):
        pass
    def create_node(self, parsed_node) -> DbcNode:
        name = parsed_node
        node = DbcNode(name)
        return node
    def create_signal(self, parsed_signal) -> DbcSignal:
        signal_name = parsed_signal["signal_name"]
        start_bit = read_int(parsed_signal["start_bit"])
        signal_size = read_int(parsed_signal["signal_size"])
        byte_order = read_byte_order(parsed_signal["byte_order"])
        value_type = read_signal_value_type(parsed_signal["value_type"])
        factor = read_float_with_default(parsed_signal["factor"], 1.0)
        offset = read_float_with_default(parsed_signal["offset"], 0.0)
        minimum = read_float_with_default(parsed_signal["minimum"], None)
        maximum = read_float_with_default(parsed_signal["maximum"], None)
        unit = read_char_string(parsed_signal["unit"])
        signal = DbcSignal(signal_name, start_bit, signal_size, byte_order, value_type, factor, offset, minimum, maximum, unit)
        return signal
    def create_message(self, parsed_message) -> DbcMessage:
        message_id = read_int(parsed_message["message_id"])
        message_name = parsed_message["message_name"]
        message_size = read_int(parsed_message["message_size"])
        transmitter = parsed_message["transmitter"]
        message = DbcMessage(message_id, message_name, message_size, transmitter)
        parsed_signals = parsed_message["signals"]
        for parsed_signal in parsed_signals:
            signal = self.create_signal(parsed_signal)
            message._add_signal(signal)
        return message
    def create_environment_variable(self, parsed_ev, nodes_by_name: Dict[str, DbcNode]) -> DbcEnvironmentVariable:
        ev_name = parsed_ev[1]
        ev_type = read_env_var_type(parsed_ev[3])
        ev_min = read_float_with_default(parsed_ev[5], None)
        ev_max = read_float_with_default(parsed_ev[7], None)
        ev_unit = read_char_string(parsed_ev[9])
        ev_ival = read_float_with_default(parsed_ev[10], None)
        ev_id = read_int(parsed_ev[11])
        ev_atype = read_env_var_access_type(parsed_ev[12])
        ev = DbcEnvironmentVariable(ev_name, ev_type, 0, ev_min, ev_max, ev_unit, ev_ival, ev_id, ev_atype)
        ev_anode = parsed_ev[13]
        if ev_anode != "Vector__XXX":
            anode = nodes_by_name[ev_anode]
            ev._add_access_node(anode)
        ev_anodes = parsed_ev[14]
        for ev_anode in ev_anodes:
            if ev_anode != "Vector__XXX":
                anode = nodes_by_name[ev_anode]
                ev._add_access_node(anode)
        return ev
    def _process_comments(self, ast, dbc: DbcFile) -> DbcFile:
        comments = ast["comments"]
        for comment in comments:
            if len(comment) == 3:
                # Global comment
                dbc.version = read_char_string(comment[1])
            elif len(comment) == 5:
                # BU_, BO_ or EV_
                object_type = comment[1]
                if object_type == "BU_":
                    node_name = comment[2]
                    node = dbc.get_node(node_name)
                    node.description = read_char_string(comment[3])
                elif object_type == "BO_":
                    msg_id = read_int(comment[2])
                    msg = dbc.get_message(msg_id)
                    msg.description = read_char_string(comment[3])
                elif object_type == "EV_":
                    ev_name = comment[2]
                    ev = dbc.get_environment_variable(ev_name)
                    ev.description = read_char_string(comment[3])
                else:
                    raise RuntimeError(f"Unexpected object type {object_type} in comment {comment}")
            elif len(comment) == 6:
                # SG_ comment
                msg_id = read_int(comment[2])
                msg = dbc.get_message(msg_id)
                signal_name = comment[3]
                signal = msg.get_signal(signal_name)
                signal.description = read_char_string(comment[4])
            else:
                raise RuntimeError(f"Unexpected token length in comment {comment}")
        return dbc
    def _process_nodes(self, ast, dbc: DbcFile) -> DbcFile:
        nodes = ast["nodes"]
        node_names = nodes["node_names"]
        for node_name in node_names:
            node = self.create_node(node_name)
            dbc._add_node(node)
        return dbc
    def _process_messages(self, ast, dbc: DbcFile) -> DbcFile:
        messages = ast["messages"]
        for message in messages:
            frame = self.create_message(message)
            dbc._add_message(frame)
        return dbc
    def _process_environment_variables(self, ast, dbc: DbcFile) -> DbcFile:
        evs = ast["environment_variables"]
        for ev in evs:
            evar = self.create_environment_variable(ev, dbc.nodes_by_name)
            dbc._add_environment_variable(evar)
        return dbc
    def _process_environment_variables_data(self, ast, dbc: DbcFile) -> DbcFile:
        ev_data = ast["environment_variables_data"]
        for evd in ev_data:
            ev_name = evd[1]
            ev = dbc.get_environment_variable(ev_name)
            data_size = read_int(evd[3])
            ev.type = DbcEnvironmentVariableType.DATA
            ev.data_size = data_size
        return dbc
    def _process_signal_type_refs(self, ast, dbc: DbcFile) -> DbcFile:
        sts = ast["signal_type_refs"]
        for st in sts:
            token = st[0]
            if token == "SIG_VALTYPE_":
                msg_id = read_int(st[1])
                msg = dbc.get_message(msg_id)
                sig_name = st[2]
                sig = msg.get_signal(sig_name)
                stype = read_extended_value_type(st[4], sig)
                sig.value_type = stype
        return dbc
    def _process_attributes(self, ast, dbc: DbcFile) -> DbcFile:
        attribute_definitions = ast["attribute_definitions"]
        for attribute_definition in attribute_definitions:
            attr_type = attribute_definition[0]
            if attr_type == "BA_DEF_" and len(attribute_definition) == 4:
                attribute_name = attribute_definition[1].name
                attribute_type = read_attribute_value_type(attribute_definition[2])
                attr = DbcAttribute(attribute_name, attribute_type, DbcAttributeObjectType.GLOBAL)
                dbc._add_attribute_definition(attr)
            elif len(attribute_definition) == 5:
                object_type = attribute_definition[1]
                attribute_name = attribute_definition[2].name
                attribute_type = read_attribute_value_type(attribute_definition[3])
                otype = DbcAttributeObjectType.GLOBAL
                if attr_type == "BA_DEF_" and object_type == "BU_":
                    otype = DbcAttributeObjectType.NODE
                elif attr_type == "BA_DEF_" and object_type == "BO_":
                    otype = DbcAttributeObjectType.MESSAGE
                elif attr_type == "BA_DEF_" and object_type == "SG_":
                    otype = DbcAttributeObjectType.SIGNAL
                elif attr_type == "BA_DEF_" and object_type == "EV_":
                    otype = DbcAttributeObjectType.ENVIRONMENT_VARIABLE
                elif attr_type == "BA_DEF_REL_" and object_type == "BU_BO_REL_":
                    otype = DbcAttributeObjectType.NODE_MESSAGE
                elif attr_type == "BA_DEF_REL_" and object_type == "BU_SG_REL_":
                    otype = DbcAttributeObjectType.NODE_SIGNAL
                elif attr_type == "BA_DEF_REL_" and object_type == "BU_EV_REL_":
                    otype = DbcAttributeObjectType.NODE_ENVIRONMENT_VARIABLE
                else:
                    raise RuntimeError(f"Unexpected object {object_type} for attribute definition")
                attr = DbcAttribute(attribute_name, attribute_type, otype)
                dbc._add_attribute_definition(attr)
            else:
                raise RuntimeError(f"Unexpected token length in attribute_definition {attribute_definition}")
        attribute_defaults = ast["attribute_defaults"]
        for attribute_default in attribute_defaults:
            attribute_name = attribute_default[1].name
            attr = dbc.get_attribute_definition(attribute_name)
            attribute_value = read_attribute_value(attribute_default[2], attr)
            attr.default = attribute_value
        attribute_values = ast["attribute_values"]
        for attribute_value in attribute_values:
            attr_type = attribute_value[0]
            if attr_type == "BA_" and len(attribute_value) == 4:
                attr_name = attribute_value[1].name
                attr = dbc.get_attribute_definition(attr_name)
                attr_value = read_attribute_value(attribute_value[2], attr)
                dbc.add_attribute_value(attr_value)
            elif attr_type == "BA_" and  len(attribute_value) == 6:
                attr_name = attribute_value[1].name
                object_type = attribute_value[2]
                attr = dbc.get_attribute_definition(attr_name)
                attr_value = read_attribute_value(attribute_value[4], attr)
                if attr_type == "BA_" and object_type == "BU_":
                    node_name = attribute_value[3]
                    node = dbc.get_node(node_name)
                    node.add_attribute(attr_value)
                elif attr_type == "BA_" and object_type == "BO_":
                    msg_id = read_int(attribute_value[3])
                    msg = dbc.get_message(msg_id)
                    msg.add_attribute(attr_value)
                elif attr_type == "BA_" and object_type == "EV_":
                    ev_name = attribute_value[3]
                    ev = dbc.get_environment_variable(ev_name)
                    ev.add_attribute(attr_value)
                else:
                    raise RuntimeError(f"Unexpected object {object_type} for attribute value")
            elif attr_type == "BA_REL_" and  len(attribute_value) == 6:
                attr_name = attribute_value[1].name
                object_type = attribute_value[2]
                attr = dbc.get_attribute_definition(attr_name)
                node_name = attribute_value[3]
                node = dbc.get_node(node_name)
                attr_value = read_attribute_value(attribute_value[4], attr)
                raise NotImplementedError(f"TODO")
            elif len(attribute_value) == 7:
                attr_name = attribute_value[1].name
                object_type = attribute_value[2]
                attr = dbc.get_attribute_definition(attr_name)
                attr_value = read_attribute_value(attribute_value[5], attr)
                if attr_type == "BA_" and object_type == "SG_":
                    msg_id = read_int(attribute_value[3])
                    msg = dbc.get_message(msg_id)
                    sig_name = attribute_value[4]
                    sig = msg.get_signal(sig_name)
                    sig.add_attribute(attr_value)
                else:
                    raise RuntimeError(f"Unexpected object {object_type} for attribute value")
            elif attr_type == "BA_REL_" and len(attribute_value) == 8:
                attr_name = attribute_value[1].name
                object_type1 = attribute_value[2]
                attr = dbc.get_attribute_definition(attr_name)
                node_name = attribute_value[3]
                node = dbc.get_node(node_name)
                object_type2 = attribute_value[4]
                attr_value = read_attribute_value(attribute_value[6], attr)
                if object_type1 == "BU_BO_REL_" and object_type2 == "BO_":
                    msg_id = read_int(attribute_value[5])
                    msg = dbc.get_message(msg_id)
                    print(f"Warning! Attribute {attr.name}:{attr_value.value} for node {node.name} and message {msg.name} ignored")
                elif object_type1 == "BU_EV_REL_" and object_type2 == "EV_":
                    ev_name = attribute_value[5]
                    ev = dbc.get_environment_variable(ev_name)
                    print(f"Warning! Attribute {attr.name}:{attr_value.value} for node {node.name} and ev {ev.name} ignored")
                else:
                    raise RuntimeError(f"Unexpected object {object_type1} for attribute value")
            elif attr_type == "BA_REL_" and len(attribute_value) == 9:
                attr_name = attribute_value[1].name
                object_type1 = attribute_value[2]
                attr = dbc.get_attribute_definition(attr_name)
                node_name = attribute_value[3]
                object_type2 = attribute_value[4]
                attr_value = read_attribute_value(attribute_value[7], attr)
                if object_type1 == "BU_SG_REL_" and object_type2 == "SG_":
                    msg_id = read_int(attribute_value[5])
                    msg = dbc.get_message(msg_id)
                    sig_name = attribute_value[6]
                    sig = msg.get_signal(sig_name)
                    print(f"Warning! Attribute {attr.name}:{attr_value.value} for node {node.name} and signal {sig.name} ignored")
                else:
                    raise RuntimeError(f"Unexpected object {object_type1} for attribute value")
            else:
                raise RuntimeError(f"Unexpected token length in attribute_value {attribute_value}")
        return dbc
    def _process_value_descriptions(self, ast, dbc: DbcFile) -> DbcFile:
        value_descriptions = ast["value_descriptions"]
        for value_description in value_descriptions:
            if len(value_description) == 5:
                msg_id = read_int(value_description[1])
                msg = dbc.get_message(msg_id)
                sig_name = value_description[2]
                sig = msg.get_signal(sig_name)
                values = value_description[3]
                for value in values:
                    val = float(value[0])
                    label = read_char_string(value[1])
                    sig.add_value_description(val, label)
            elif len(value_description) == 4:
                ev_name = value_description[1]
                ev = dbc.get_environment_variable(ev_name)
                values = value_description[2]
                for value in values:
                    val = float(value[0])
                    label = read_char_string(value[1])
                    ev.add_value_description(val, label)
            else:
                raise RuntimeError(f"Unexpected token length in value_description {value_description}")
        return dbc
    def _process_signal_groups(self, ast, dbc: DbcFile) -> DbcFile:
        signal_groups = ast["signal_groups"]
        for signal_group in signal_groups:
            msg_id = read_int(signal_group[1])
            msg = dbc.get_message(msg_id)
            sig_gp_name = signal_group[2]
            repetitions = read_int(signal_group[3])
            sig_gp = DbcSignalGroup(sig_gp_name, repetitions)
            signal_names = signal_group[5]
            for signal_name in signal_names:
                sig = msg.get_signal(signal_name)
                sig_gp._add_signal(sig)
            msg._add_signal_group(sig_gp)
        return dbc
    def _process_version(self, ast, dbc: DbcFile) -> DbcFile:
        if ast["version"] is not None:
            parsed_version = ast["version"]
            version = read_char_string(parsed_version[1])
            dbc.version = version
        return dbc
    def _process_value_tables(self, ast, dbc: DbcFile) -> DbcFile:
        vtables = ast["value_tables"]
        for vtable in vtables:
            name = vtable[1]
            vt = DbcValueTable(name)
            values = vtable[2]
            for value in values:
                val = read_float(value[0])
                label = read_char_string(value[1])
                vt._add_value(val, label)
            dbc._add_value_table(vt)
        return dbc
    def create_dbc(self, grammar: str, text: str) -> DbcFile:
        dbc = DbcFile()
        ast = tatsu_parse(grammar, text)
        dbc = self._process_version(ast, dbc)
        dbc = self._process_nodes(ast, dbc)
        dbc = self._process_value_tables(ast, dbc)
        dbc = self._process_messages(ast, dbc)
        dbc = self._process_environment_variables(ast, dbc)
        dbc = self._process_environment_variables_data(ast, dbc)
        dbc = self._process_comments(ast, dbc)
        dbc = self._process_attributes(ast, dbc)
        dbc = self._process_value_descriptions(ast, dbc)
        dbc = self._process_signal_type_refs(ast, dbc)
        dbc = self._process_signal_groups(ast, dbc)
        return dbc

def parse_dbc(filename: str) -> Dict[str, DbcMessage]:
    dbc = Path(filename)
    if not dbc.exists():
        raise RuntimeError(f"Wrong DBC path {dbc}")
    with dbc.open('r') as infile:
        text = infile.read()
    return parse_text(text)

def parse_text(text: str) -> DbcFile:
    factory = DbcFactory()
    grammar_file = Path('grammar.ebnf')
    if not grammar_file.exists():
        raise RuntimeError(f"Wrong grammar file {grammar_file}")
    grammar = grammar_file.read_text()
    dbc = factory.create_dbc(grammar, text)
    return dbc

def main():
    parse_dbc("")

if __name__ == '__main__':
    #parser = argparse.ArgumentParser(description = '')
    #parser.add_argument('dbc', help='Input DBC')
    #args = parser.parse_args()
    main()