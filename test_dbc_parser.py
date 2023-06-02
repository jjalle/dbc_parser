import pytest

from parser_tatsu import DbcFactory, DbcMessage, DbcSignal, parse_dbc, parse_text, DbcSignalByteOrder, DbcSignalValueType, DbcEnvironmentVariableType, DbcEnvironmentVariableAccessType, DbcAttributeObjectType, DbcAttributeType, read_char_string

class Setup:
    def __init__(self):
        self.factory = DbcFactory()

@pytest.fixture
def setup() -> Setup:
    return Setup()

def test_version(setup: Setup):
    text = r'''
VERSION "TEST"

BS_:

BU_:
'''
    dbc = parse_text(text)
    assert dbc.version == "TEST"

def test_ns(setup: Setup):
    text = r'''
VERSION "TEST"

NS_ :
	NS_DESC_
	CM_
	BA_DEF_
	BA_
	VAL_
	CAT_DEF_
	CAT_
	FILTER
	BA_DEF_DEF_
	EV_DATA_
	ENVVAR_DATA_
	SGTYPE_
	SGTYPE_VAL_
	BA_DEF_SGTYPE_
	BA_SGTYPE_
	SIG_TYPE_REF_
	VAL_TABLE_
	SIG_GROUP_
	SIG_VALTYPE_
	SIGTYPE_VALTYPE_
	BO_TX_BU_
	BA_DEF_REL_
	BA_REL_
	BA_DEF_DEF_REL_
	BU_SG_REL_
	BU_EV_REL_
	BU_BO_REL_
	SG_MUL_VAL_

BS_:

BU_:
'''
    dbc = parse_text(text)
    assert dbc.version == "TEST"

def test_ns_with_typo(setup: Setup):
    text = r'''
VERSION "TEST"

NS_ :
	NS_DESC_
	CM_
	BA_DEF_
	BA_
	VAL_
	CAT_DEF_
	CAT_
	FILTER
	BA_DEF_DEF_
	EV_DATA
	ENVVAR_DATA_
	SGTYPE_
	SGTYPE_VAL_
	BA_DEF_SGTYPE_
	BA_SGTYPE_
	SIG_TYPE_REF_
	VAL_TABLE_
	SIG_GROUP_
	SIG_VALTYPE_
	SIGTYPE_VALTYPE_
	BO_TX_BU_
	BA_DEF_REL_
	BA_REL_
	BA_DEF_DEF_REL_
	BU_SG_REL_
	BU_EV_REL_
	BU_BO_REL_
	SG_MUL_VAL_

BS_:

BU_:
'''
    dbc = parse_text(text)
    assert dbc.version == "TEST"

def test_node(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2
'''
    dbc = parse_text(text)
    assert dbc.has_node("NODE1")
    assert dbc.has_node("NODE2")
    node1 = dbc.get_node("NODE1")
    node2 = dbc.get_node("NODE2")
    assert node1.name == "NODE1"
    assert node2.name == "NODE2"

def test_value_table(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

VAL_TABLE_ vtname 1 "LABEL1" 2 "LABEL2";
'''
    dbc = parse_text(text)
    assert dbc.has_value_table("vtname")
    vt = dbc.get_value_table("vtname")
    assert len(vt.values) == 2
    label1, val1 = vt.values[0]
    label2, val2 = vt.values[1]
    assert "LABEL1" == label1
    assert "LABEL2" == label2
    assert val1 == 1
    assert val2 == 2

def test_value_table_duplicated(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

VAL_TABLE_ vtname 1 "LABEL1" 2 "LABEL2" 3 "Not used" 4 "Not used";
'''
    dbc = parse_text(text)
    assert dbc.has_value_table("vtname")
    vt = dbc.get_value_table("vtname")
    assert len(vt.values) == 4
    label1, val1 = vt.values[0]
    label2, val2 = vt.values[1]
    label3, val3 = vt.values[2]
    label4, val4 = vt.values[3]
    assert "LABEL1" == label1
    assert "LABEL2" == label2
    assert "Not used" == label3
    assert "Not used" == label4
    assert val1 == 1
    assert val2 == 2
    assert val3 == 3
    assert val4 == 4


def test_comment(setup: Setup):
    text = r'''
BS_:

BU_:

CM_ "COM_MATRIX";
'''
    dbc = parse_text(text)
    assert dbc.version == "COM_MATRIX"

def test_comment_node(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

CM_ BU_ NODE1 "Node 1";
'''
    dbc = parse_text(text)
    node = dbc.get_node("NODE1")
    assert node.description == "Node 1"

def test_comment_message(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

BO_ 123 MESSAGE1: 8 NODE1

CM_ BO_ 123 "Message 1";
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    assert msg.description == "Message 1"

def test_comment_signal(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|0] ""  NODE2

CM_ SG_ 123 SIGNAL11 "Signal 11";
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("SIGNAL11")
    assert sig.description == "Signal 11"

def test_comment_ev(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

EV_ EVAR1: 0 [-10|10] "" 0 1 DUMMY_NODE_VECTOR0  NODE1;

CM_ EV_ EVAR1 "Evar 1";
'''
    dbc = parse_text(text)
    ev = dbc.get_environment_variable("EVAR1")
    assert ev.description == "Evar 1"

def test_message1(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|0] ""  NODE2
 SG_ SIGNAL12 : 18|2@1+ (1,0) [0|0] ""  NODE2
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    assert msg.name == "MESSAGE1"
    assert msg.id == 123
    assert msg.size == 8
    assert msg.transmitter.name == "NODE1"
    assert len(msg.signals_by_name) == 2

def test_message2(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

BO_ 123 MESSAGE1: 8 NODE1
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    assert msg.name == "MESSAGE1"
    assert msg.id == 123
    assert msg.size == 8
    assert len(msg.signals_by_name) == 0

def test_message_transmitter(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2 NODE3

BO_ 123 MESSAGE1: 8 NODE1

BO_TX_BU_ 123 : NODE2,NODE3;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    assert msg.name == "MESSAGE1"
    assert msg.id == 123
    assert msg.size == 8
    assert len(msg.signals_by_name) == 0

def test_signal(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2 NODE3

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|10] ""  NODE2,NODE3
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("SIGNAL11")
    assert sig.name == "SIGNAL11"
    assert sig.byte_order == DbcSignalByteOrder.BIG_ENDIAN
    assert sig.value_type == DbcSignalValueType.UNSIGNED
    assert sig.factor == 1
    assert sig.offset == 0
    assert sig.minimum == 0
    assert sig.maximum == 10
    assert sig.start_bit == 18
    assert sig.size == 2
    assert len(sig.receivers) == 2
    assert sig.receivers[0].name == "NODE2"
    assert sig.receivers[1].name == "NODE3"

def test_signal_value_description(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|10] ""  NODE2

VAL_ 123 SIGNAL11 1 "LABEL1" 2 "LABEL2" ;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("SIGNAL11")
    assert sig.name == "SIGNAL11"
    assert len(sig.value_descriptions) == 2
    assert sig.value_descriptions[0][0] == 1
    assert sig.value_descriptions[0][1] == "LABEL1"
    assert sig.value_descriptions[1][0] == 2
    assert sig.value_descriptions[1][1] == "LABEL2"

def test_signal_extended_type(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|10] ""  NODE2

SIG_VALTYPE_ 123 SIGNAL11 : 2;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("SIGNAL11")
    assert sig.value_type == DbcSignalValueType.FLOAT64

def test_signal_cm_name(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ CM_SIGNAL11 : 18|2@1+ (1,0) [0|10] ""  NODE2

SIG_VALTYPE_ 123 CM_SIGNAL11 : 2;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("CM_SIGNAL11")
    assert sig.value_type == DbcSignalValueType.FLOAT64

def test_ev(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

EV_ EVAR1: 0 [-10|10] "UNIT" 0 1 DUMMY_NODE_VECTOR0  NODE1;
'''
    dbc = parse_text(text)
    ev = dbc.get_environment_variable("EVAR1")
    assert ev.name == "EVAR1"
    assert ev.id == 1
    assert ev.init_value == 0
    assert ev.unit == "UNIT"
    assert ev.minimum == -10
    assert ev.maximum == 10
    assert ev.type == DbcEnvironmentVariableType.INTEGER
    assert ev.access_type == DbcEnvironmentVariableAccessType.UNRESTRICTED
    assert len(ev.access_nodes) == 1
    assert ev.access_nodes[0].name == "NODE1"


def test_ev_value(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

EV_ EVAR1: 0 [-10|10] "UNIT" 0 1 DUMMY_NODE_VECTOR0  NODE1;

VAL_ EVAR1 1 "LABEL1" 2 "LABEL2" ;
'''
    dbc = parse_text(text)
    ev = dbc.get_environment_variable("EVAR1")
    assert len(ev.value_descriptions) == 2
    assert ev.value_descriptions[0][0] == 1
    assert ev.value_descriptions[0][1] == "LABEL1"
    assert ev.value_descriptions[1][0] == 2
    assert ev.value_descriptions[1][1] == "LABEL2"

def test_ev_data(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

EV_ EVAR1: 0 [-10|10] "UNIT" 0 1 DUMMY_NODE_VECTOR0  NODE1;

ENVVAR_DATA_ EVAR1: 6;
'''
    dbc = parse_text(text)
    ev = dbc.get_environment_variable("EVAR1")
    assert ev.type == DbcEnvironmentVariableType.DATA
    assert ev.data_size == 6

def test_ev_name_with_ev(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

EV_ EV_EVAR1: 0 [-10|10] "UNIT" 0 1 DUMMY_NODE_VECTOR0  NODE1;
'''
    dbc = parse_text(text)
    ev = dbc.get_environment_variable("EV_EVAR1")
    assert ev.name == "EV_EVAR1"

def test_ev_missing_node(setup: Setup):
    text = r'''
BS_:

BU_: NODE1

EV_ EVAR1: 0 [-10|10] "UNIT" 0 1 DUMMY_NODE_VECTOR0  NODE2;
'''
    dbc = parse_text(text)
    ev = dbc.get_environment_variable("EVAR1")
    assert len(ev.access_nodes) == 1
    node = ev.access_nodes[0]
    assert node.name == "NODE2"

def test_ev_multiple_node(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

EV_ EVAR1: 0 [-10|10] "UNIT" 0 1 DUMMY_NODE_VECTOR0  NODE1,NODE2;
'''
    dbc = parse_text(text)
    ev = dbc.get_environment_variable("EVAR1")
    assert len(ev.access_nodes) == 2
    node1 = ev.access_nodes[0]
    assert node1.name == "NODE1"
    node2 = ev.access_nodes[1]
    assert node2.name == "NODE2"

def test_attribute(setup: Setup):
    text = r'''
BS_:

BU_:

BA_DEF_ "ATTR" STRING ;
BA_DEF_DEF_ "ATTR" "DEFAULT";
BA_ "ATTR" "VALUE";
'''
    dbc = parse_text(text)
    attr = dbc.get_attribute_value("ATTR")
    assert attr.name == "ATTR"
    assert attr.value == "VALUE"
    assert attr.attribute.default.value == "DEFAULT"
    assert attr.attribute.value_type.is_string()
    assert attr.attribute.object_type == DbcAttributeObjectType.GLOBAL

def test_attribute_message(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1

BA_DEF_ BO_  "ATTR" INT 0 0;
BA_DEF_DEF_  "ATTR" 0;
BA_ "ATTR" BO_ 123 2660;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    assert msg.has_attribute("ATTR")
    attr = msg.get_attribute("ATTR")
    assert attr.name == "ATTR"
    assert attr.value == 2660
    assert attr.attribute.default.value == 0
    assert attr.attribute.value_type.is_integer()
    assert attr.attribute.object_type == DbcAttributeObjectType.MESSAGE

def test_attribute_signal(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|10] ""  NODE2

BA_DEF_ SG_  "ATTR" INT 0 0;
BA_DEF_DEF_  "ATTR" 0;
BA_ "ATTR" SG_ 123 SIGNAL11 2660;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("SIGNAL11")
    assert sig.has_attribute("ATTR")
    attr = sig.get_attribute("ATTR")
    assert attr.name == "ATTR"
    assert attr.value == 2660
    assert attr.attribute.default.value == 0
    assert attr.attribute.value_type.is_integer()
    assert attr.attribute.object_type == DbcAttributeObjectType.SIGNAL

def test_attribute_signal_dup(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|10] ""  NODE2

BA_DEF_ SG_  "ATTR" INT 0 0;
BA_DEF_DEF_  "ATTR" 0;
BA_ "ATTR" SG_ 123 SIGNAL11 2660;
BA_ "ATTR" SG_ 123 SIGNAL11 2660;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("SIGNAL11")
    assert sig.has_attribute("ATTR")
    attr = sig.get_attribute("ATTR")
    assert attr.name == "ATTR"
    assert attr.value == 2660
    assert attr.attribute.default.value == 0
    assert attr.attribute.value_type.is_integer()
    assert attr.attribute.object_type == DbcAttributeObjectType.SIGNAL

def test_attribute_ev(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

EV_ EVAR1: 0 [-10|10] "UNIT" 0 1 DUMMY_NODE_VECTOR0  NODE1;

BA_DEF_ EV_  "ATTR" INT 0 0;
BA_DEF_DEF_  "ATTR" 0;
BA_ "ATTR" EV_ EVAR1 2660;
'''
    dbc = parse_text(text)
    ev = dbc.get_environment_variable("EVAR1")
    assert ev.has_attribute("ATTR")
    attr = ev.get_attribute("ATTR")
    assert attr.name == "ATTR"
    assert attr.value == 2660
    assert attr.attribute.default.value == 0
    assert attr.attribute.value_type.is_integer()
    assert attr.attribute.object_type == DbcAttributeObjectType.ENVIRONMENT_VARIABLE

def test_attribute_node_signal(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|10] ""  NODE2

BA_DEF_REL_ BU_SG_REL_  "ATTR" INT 0 65535;
BA_DEF_DEF_REL_ "ATTR" 0;
BA_REL_ "ATTR" BU_SG_REL_ NODE1 SG_ 123 SIGNAL11 3000;
BA_REL_ "ATTR" BU_SG_REL_ NODE2 SG_ 123 SIGNAL11 4000;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("SIGNAL11")
    assert sig.has_node_attribute("ATTR")
    attrs = sig.get_node_attribute("ATTR")
    assert "NODE1" in attrs
    assert "NODE2" in attrs
    attr1 = attrs["NODE1"]
    attr2 = attrs["NODE2"]
    assert attr1.name == "ATTR"
    assert attr1.value == 3000
    assert attr2.name == "ATTR"
    assert attr2.value == 4000

def test_attribute_node_signal_dup(setup: Setup):
    text = r'''
BS_:

BU_: NODE1 NODE2

BO_ 123 MESSAGE1: 8 NODE1
 SG_ SIGNAL11 : 18|2@1+ (1,0) [0|10] ""  NODE2

BA_DEF_REL_ BU_SG_REL_  "ATTR" INT 0 65535;
BA_DEF_DEF_REL_ "ATTR" 0;
BA_REL_ "ATTR" BU_SG_REL_ NODE1 SG_ 123 SIGNAL11 3000;
BA_REL_ "ATTR" BU_SG_REL_ NODE1 SG_ 123 SIGNAL11 3000;
'''
    dbc = parse_text(text)
    msg = dbc.get_message(123)
    sig = msg.get_signal("SIGNAL11")
    assert sig.has_node_attribute("ATTR")
    attrs = sig.get_node_attribute("ATTR")
    assert "NODE1" in attrs
    attr1 = attrs["NODE1"]
    assert attr1.name == "ATTR"
    assert attr1.value == 3000