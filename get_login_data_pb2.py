"""Minimal GetLoginDataRes schema, isolated from thunderFF's conflicting MajorLoginRes."""
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

_file = descriptor_pb2.FileDescriptorProto()
_file.name = 'anurag_get_login_data.proto'
_file.package = 'anurag_login_data'
_file.syntax = 'proto3'
_msg = _file.message_type.add()
_msg.name = 'GetLoginDataRes'
for name, number in [('nickname', 4), ('functional_addrs', 14), ('informational_addrs', 32)]:
    field = _msg.field.add()
    field.name = name
    field.number = number
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
_pool = descriptor_pool.DescriptorPool()
_desc = _pool.AddSerializedFile(_file.SerializeToString())
GetLoginDataRes = message_factory.GetMessageClass(_desc.message_types_by_name['GetLoginDataRes'])
