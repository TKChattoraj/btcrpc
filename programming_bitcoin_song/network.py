import socket
import time

from io import BytesIO
from random import randint
from unittest import TestCase

from block import Block
from helper import (
    hash256,
    encode_varint,
    int_to_little_endian,
    little_endian_to_int,
    read_varint,
)

TX_DATA_TYPE = 1
BLOCK_DATA_TYPE = 2
FILTERED_BLOCK_DATA_TYPE = 3
COMPACT_BLOCK_DATA_TYPE = 4

NETWORK_MAGIC = b'\xf9\xbe\xb4\xd9'
TESTNET_NETWORK_MAGIC = b'\x0b\x11\x09\x07'


class NetworkEnvelope:

    def __init__(self, command, payload, testnet=False):
        self.command = command
        self.payload = payload
        if testnet:
            self.magic = TESTNET_NETWORK_MAGIC
        else:
            self.magic = NETWORK_MAGIC

    def __repr__(self):
        return '{}: {}'.format(
            self.command.decode('ascii'),
            self.payload.hex(),
        )
  

    @classmethod
    def parse(cls, s, testnet=False):
        '''Takes a stream and creates a NetworkEnvelope'''
        # check the network magic
        magic = s.read(4)
        if magic == b'':
            raise RuntimeError('Connection reset!')
        if testnet:
            expected_magic = TESTNET_NETWORK_MAGIC
        else:
            expected_magic = NETWORK_MAGIC
        if magic != expected_magic:
            raise RuntimeError('magic is not right {} vs {}'.format(magic.hex(), expected_magic.hex()))
        
        command = s.read(12).rstrip(b'\00')
        payload_length = little_endian_to_int(s.read(4))
        payload_checksum = s.read(4)
        payload = s.read(payload_length)
        payload_hash256 = hash256(payload)
        if payload_hash256[:4] != payload_checksum:
            raise RuntimeError('payload is not correct.  Checksum does not check out')
        else:
            envelope = NetworkEnvelope(command, payload, testnet=testnet)
            return envelope

        # command 12 bytes
        # strip the trailing 0's
        # payload length 4 bytes, little endian
        # checksum 4 bytes, first four of hash256 of payload
        # payload is of length payload_length
        # verify checksum
        # return an instance of the class
        #raise NotImplementedError

    def serialize(self):
        '''Returns the byte serialization of the entire network message'''

        result = b''
        result += self.magic
        result += self.command.ljust(12, b'\00')
        result += int_to_little_endian(len(self.payload), 4)
        result += hash256(self.payload)[:4]
        result += self.payload
        return result

        # add the network magic
        # command 12 bytes
        # fill with 0's
        # payload length 4 bytes, little endian
        # checksum 4 bytes, first four of hash256 of payload
        # payload
        # raise NotImplementedError


    def stream(self):
        '''Returns a stream for parsing the payload'''
        return BytesIO(self.payload)


class NetworkEnvelopeTest(TestCase):

    def test_parse(self):
        msg = bytes.fromhex('f9beb4d976657261636b000000000000000000005df6e0e2')
        stream = BytesIO(msg)
        envelope = NetworkEnvelope.parse(stream)
        self.assertEqual(envelope.command, b'verack')
        self.assertEqual(envelope.payload, b'')
        msg = bytes.fromhex('f9beb4d976657273696f6e0000000000650000005f1a69d2721101000100000000000000bc8f5e5400000000010000000000000000000000000000000000ffffc61b6409208d010000000000000000000000000000000000ffffcb0071c0208d128035cbc97953f80f2f5361746f7368693a302e392e332fcf05050001')
        stream = BytesIO(msg)
        envelope = NetworkEnvelope.parse(stream)
        print(envelope.command)
        self.assertEqual(envelope.command, b'version')
        self.assertEqual(envelope.payload, msg[24:])

    def test_serialize(self):
        msg = bytes.fromhex('f9beb4d976657261636b000000000000000000005df6e0e2')
        stream = BytesIO(msg)
        envelope = NetworkEnvelope.parse(stream)
        self.assertEqual(envelope.serialize(), msg)
        msg = bytes.fromhex('f9beb4d976657273696f6e0000000000650000005f1a69d2721101000100000000000000bc8f5e5400000000010000000000000000000000000000000000ffffc61b6409208d010000000000000000000000000000000000ffffcb0071c0208d128035cbc97953f80f2f5361746f7368693a302e392e332fcf05050001')
        stream = BytesIO(msg)
        envelope = NetworkEnvelope.parse(stream)
        self.assertEqual(envelope.serialize(), msg)


# tag::source2[]
class VersionMessage:
    command = b'version'

    def __init__(self, version=70015, services=0, timestamp=None,
                 receiver_services=0,
                 receiver_ip=b'\x00\x00\x00\x00', receiver_port=8333,
                 sender_services=0,
                 sender_ip=b'\x00\x00\x00\x00', sender_port=8333,
                 nonce=None, user_agent=b'/programmingbitcoin:0.1/',
                 latest_block=0, relay=False):
        self.version = version
        self.services = services
        if timestamp is None:
            self.timestamp = int(time.time())
        else:
            self.timestamp = timestamp
        self.receiver_services = receiver_services
        self.receiver_ip = receiver_ip
        self.receiver_port = receiver_port
        self.sender_services = sender_services
        self.sender_ip = sender_ip
        self.sender_port = sender_port
        if nonce is None:
            self.nonce = int_to_little_endian(randint(0, 2**64), 8)
        else:
            self.nonce = nonce
        self.user_agent = user_agent
        self.latest_block = latest_block
        self.relay = relay
    # end::source2[]

    def serialize(self):
        '''Serialize this message to send over the network'''

        result = b''
        result += self.version.to_bytes(4, byteorder='little')
        result += self.services.to_bytes(8, byteorder='little')
        result += self.timestamp.to_bytes(8, byteorder='little')
        result += self.receiver_services.to_bytes(8, byteorder='little')
        result += bytes.fromhex('00000000000000000000ffff')
        result += self.receiver_ip
        result += self.receiver_port.to_bytes(2, byteorder='big')
        result += self.sender_services.to_bytes(8, byteorder='little')
        result += bytes.fromhex('00000000000000000000ffff')
        result += self.sender_ip
        result += self.sender_port.to_bytes(2, byteorder='big')
        result += self.nonce
        result += encode_varint(len(self.user_agent))
        result += self.user_agent
        result += int_to_little_endian(self.latest_block, 4)
        if self.relay:
            result += b'\x01'
        else:
            result += b'\x00'
        return result



        # version is 4 bytes little endian
        # services is 8 bytes little endian
        # timestamp is 8 bytes little endian
        # receiver services is 8 bytes little endian
        # IPV4 is 10 00 bytes and 2 ff bytes then receiver ip
        # receiver port is 2 bytes, big endian
        # sender services is 8 bytes little endian
        # IPV4 is 10 00 bytes and 2 ff bytes then sender ip
        # sender port is 2 bytes, big endian
        # nonce should be 8 bytes
        # useragent is a variable string, so varint first
        # latest block is 4 bytes little endian
        # relay is 00 if false, 01 if true
        # raise NotImplementedError


class VersionMessageTest(TestCase):

    def test_serialize(self):
        v = VersionMessage(timestamp=0, nonce=b'\x00' * 8)
        self.assertEqual(v.serialize().hex(), '7f11010000000000000000000000000000000000000000000000000000000000000000000000ffff00000000208d000000000000000000000000000000000000ffff00000000208d0000000000000000182f70726f6772616d6d696e67626974636f696e3a302e312f0000000000')


# tag::source3[]
class VerAckMessage:
    command = b'verack'

    def __init__(self):
        pass

    @classmethod
    def parse(cls, s):
        return cls()

    def serialize(self):
        return b''
# end::source3[]


class PingMessage:
    command = b'ping'

    def __init__(self, nonce):
        self.nonce = nonce

    @classmethod
    def parse(cls, s):
        nonce = s.read(8)
        return cls(nonce)

    def serialize(self):
        return self.nonce


class PongMessage:
    command = b'pong'

    def __init__(self, nonce):
        self.nonce = nonce

    @classmethod
    def parse(cls, s):
        nonce = s.read(8)
        return cls(nonce)

    def serialize(self):
        return self.nonce


# tag::source5[]
class GetHeadersMessage:
    command = b'getheaders'

    def __init__(self, version=70015, num_hashes=1, 
        start_block=None, end_block=None):
        self.version = version
        self.num_hashes = num_hashes  # <1>
        if start_block is None:  # <2>
            raise RuntimeError('a start block is required')
        self.start_block = start_block
        if end_block is None:
            self.end_block = b'\x00' * 32  # <3>
        else:
            self.end_block = end_block
    # end::source5[]

    def serialize(self):
        '''Serialize this message to send over the network'''

        result = b''
        result += int_to_little_endian(self.version, 4)
        result += encode_varint(self.num_hashes)
        result += self.start_block[::-1]
        result += self.end_block[::-1]
        return result


        # protocol version is 4 bytes little-endian
        # number of hashes is a varint
        # start block is in little-endian
        # end block is also in little-endian


class GetHeadersMessageTest(TestCase):

    def test_serialize(self):
        block_hex = '0000000000000000001237f46acddf58578a37e213d2a6edc4884a2fcad05ba3'
        gh = GetHeadersMessage(start_block=bytes.fromhex(block_hex))
        self.assertEqual(gh.serialize().hex(), '7f11010001a35bd0ca2f4a88c4eda6d213e2378a5758dfcd6af437120000000000000000000000000000000000000000000000000000000000000000000000000000000000')


# tag::source6[]
class HeadersMessage:
    command = b'headers'

    def __init__(self, blocks):
        self.blocks = blocks

    @classmethod
    def parse(cls, stream):
        num_headers = read_varint(stream)
        blocks = []
        for _ in range(num_headers):
            blocks.append(Block.parse(stream))  # <1>
            num_txs = read_varint(stream)  # <2>
            if num_txs != 0:  # <3>
                raise RuntimeError('number of txs not 0')
        return cls(blocks)
    # end::source6[]


class HeadersMessageTest(TestCase):

    def test_parse(self):
        hex_msg = '0200000020df3b053dc46f162a9b00c7f0d5124e2676d47bbe7c5d0793a500000000000000ef445fef2ed495c275892206ca533e7411907971013ab83e3b47bd0d692d14d4dc7c835b67d8001ac157e670000000002030eb2540c41025690160a1014c577061596e32e426b712c7ca00000000000000768b89f07044e6130ead292a3f51951adbd2202df447d98789339937fd006bd44880835b67d8001ade09204600'
        stream = BytesIO(bytes.fromhex(hex_msg))
        headers = HeadersMessage.parse(stream)
        self.assertEqual(len(headers.blocks), 2)
        for b in headers.blocks:
            self.assertEqual(b.__class__, Block)

class GetDataMessage:
    command = b'getdata'

    def __init__(self):
        self.data = []  # <1>

    def add_data(self, data_type, identifier):
        self.data.append((data_type, identifier))  # <2>
    # end::source1[]

    def serialize(self):
        result = b''
        result += encode_varint(len(self.data))
        for datum in self.data:
            data_type, identifier = datum
            result += int_to_little_endian(data_type, 4)
            result += identifier[::-1]
        return result

        # start with the number of items as a varint
        # loop through each tuple (data_type, identifier) in self.data
            # data type is 4 bytes Little-Endian
            # identifier needs to be in Little-Endian

class GetDataMessageTest(TestCase):

    def test_serialize(self):
        hex_msg = '020300000030eb2540c41025690160a1014c577061596e32e426b712c7ca00000000000000030000001049847939585b0652fba793661c361223446b6fc41089b8be00000000000000'
        get_data = GetDataMessage()
        block1 = bytes.fromhex('00000000000000cac712b726e4326e596170574c01a16001692510c44025eb30')
        get_data.add_data(FILTERED_BLOCK_DATA_TYPE, block1)
        block2 = bytes.fromhex('00000000000000beb88910c46f6b442312361c6693a7fb52065b583979844910')
        get_data.add_data(FILTERED_BLOCK_DATA_TYPE, block2)
        self.assertEqual(get_data.serialize().hex(), hex_msg)





class GenericMessage:
    def __init__(self, command, payload):
        self.command = command
        self.payload = payload

    def serialize(self):
        return self.payload


# tag::source4[]
class SimpleNode:

    def __init__(self, host, port=None, testnet=False, logging=False):
        if port is None:
            if testnet:
                port = 18333
            else:
                port = 8333
        self.testnet = testnet
        self.logging = logging
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.stream = self.socket.makefile('rb', None)
    # end::source4[]

    def handshake(self):
        '''Do a handshake with the other node.
        Handshake is sending a version message and getting a verack back.'''
        version = VersionMessage()
        self.send(version)
        self.wait_for(VerAckMessage)
        # create a version message
        # send the command
        # wait for a
        # verack message
    # tag::source4[]

    def send(self, message):  # <1>
        '''Send a message to the connected node'''
        envelope = NetworkEnvelope(
            message.command, message.serialize(), testnet=self.testnet)
        if self.logging:
            print('sending: {}'.format(envelope))
        self.socket.sendall(envelope.serialize())

    def read(self):  # <2>
        '''Read a message from the socket'''
        envelope = NetworkEnvelope.parse(self.stream, testnet=self.testnet)
        if self.logging:
            print('receiving: {}'.format(envelope))
        return envelope

    def wait_for(self, *message_classes):  # <3>
        '''Wait for one of the messages in the list'''
        command = None
        command_to_class = {m.command: m for m in message_classes}
        while command not in command_to_class.keys():
            envelope = self.read()
            command = envelope.command
            if command == VersionMessage.command:
                self.send(VerAckMessage())
            elif command == PingMessage.command:
                self.send(PongMessage(envelope.payload))
        return command_to_class[command].parse(envelope.stream())
# end::source4[]


class SimpleNodeTest(TestCase):

    def test_handshake(self):
        node = SimpleNode('testnet.programmingbitcoin.com', testnet=True)
        node.handshake()