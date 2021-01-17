import os
import sys
import logging
import time

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'gen-py'))

from comm.CommonService import Processor

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from flask import Flask, Response, abort
from prometheus_client import multiprocess, REGISTRY, PlatformCollector, Info
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST, Gauge, Counter, ProcessCollector

from threading import Thread

logger = logging.getLogger('root')

app = Flask(__name__)

IN_PROGRESS = Gauge("inprogress_requests", "Test gauge", multiprocess_mode='livesum')
NUM_REQUESTS = Counter("num_requests", "Example counter")

@app.route('/hello', methods=['GET'])
def hello_from_flask():
    return "happy from flask"

@app.route("/metrics", methods=['GET'])
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)

    i = Info('build_info', "The build information", registry=registry)
    i.info({"version": "1,2,3"})

    data = generate_latest(registry)
    return Response(data, mimetype=CONTENT_TYPE_LATEST)

@app.route("/health", methods=['GET'])
def isHealthy():
    tsocker = TSocket.TSocket('localhost', 9000)
    transport = TTransport.TBufferedTransport(tsocker)

    try:
        transport.open()
    except Exception as e:
        return Response("unhealthy", mimetype="text/plain", status=400)
    finally:
        transport.close()

    return Response("healthy", mimetype="text/plain")

class ServiceHandler:

    @IN_PROGRESS.track_inprogress()
    def echo(self, msg):
        NUM_REQUESTS.inc()
        print(f"received: {msg}")
        time.sleep(5)
        return msg


class FlaskThread(Thread):

    def run(self):
        app.run(host='127.0.0.1', port=9091, debug=False)


if __name__ == '__main__':
    print("Start flask thread...")
    flask_server = FlaskThread()
    flask_server.daemon = True
    flask_server.start()

    print("Start RPC server...")
    handler = ServiceHandler()

    process = Processor(handler)

    transport = TSocket.TServerSocket('localhost', 9000)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    rpcServer = TServer.TSimpleServer(process, transport, tfactory, pfactory)

    print('starting the rpc server at localhost:9000')
    #rpcServer.serve()
    print('done')

    time.sleep(200)
