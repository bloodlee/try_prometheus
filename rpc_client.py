import os
import sys
import logging

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'gen-py'))

from comm.CommonService import Client

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

logger = logging.getLogger('root')

if __name__ == '__main__':

    try:
        tsocker = TSocket.TSocket('localhost', 9000)
        transport = TTransport.TBufferedTransport(tsocker)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = Client(protocol)

        transport.open()

        rtn = client.echo("hello, this is client!")
        print(f"received echo from server: {rtn}")

        transport.close()
    except Thrift.TException as ex:
        print(ex.message)
