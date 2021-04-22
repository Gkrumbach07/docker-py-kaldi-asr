import os
import logging
import json
from time import time, sleep
from optparse import OptionParser
from flask import Flask, request

from asr import ASR, ASR_ENGINE_NNET3
import numpy as np

from kafka import KafkaProducer

DEFAULT_HOST      = ''
DEFAULT_PORT      = 8080

DEFAULT_MODEL_DIR = '/opt/kaldi-model'
DEFAULT_MODEL     = 'model'
DEFAULT_ACOUSTIC_SCALE           = 1.0
DEFAULT_BEAM                     = 7.0
DEFAULT_FRAME_SUBSAMPLING_FACTOR = 3

DEFAULT_VF_LOGIN  = 'anonymous'
DEFAULT_REC_DIR   = '/opt/data/recordings'
SAMPLE_RATE       = 16000

# globals
kaldi_model_dir = None
kaldi_model = None
producer = None
last_broker = None
asr = None


app = Flask(__name__)

@app.route('/')
def info():
    return 'Use /decode to decode audio.'


@app.route('/decode', methods=['POST'])
def decode():
    try:
        audio       = request.json['audio']
        rate       = request.json['sample_rate']
        do_finalize = request.json['do_finalize']
        id          = request.json['id']
        broker      = request.json['broker']
        topic       = request.json['topic']
    except Exception as e:
        logging.error(e)
        return {'hstr': 'load error', 'confidence': 1}

    if rate ==  None:
        rate = SAMPLE_RATE

    hstr, confidence = asr.decode(audio, do_finalize, stream_id=id, sample_rate=rate)

    # kafka produce
    logging.info("%s, %s" % (broker, topic))

    if broker and topic:
        global producer
        global last_broker
        try:
            ssl_cert_path = os.getenv("SSL_CERT_PATH", None)
            
            if last_broker != broker or producer == None:
                if ssl_cert_path != None:
                    producer = KafkaProducer(bootstrap_servers=broker, security_protocol="SSL", ssl_cafile=ssl_cert_path)
                else:
                    producer = KafkaProducer(bootstrap_servers=broker)
                last_broker = broker
                logging.info ("New producer: %s", broker)

            data = {
                'sentence': hstr,
                'id': id
            }
            producer.send(topic, json.dumps(data).encode('utf-8'))
            logging.info ("Pruducer (%s) sent successfully to topic (%s)" % (broker, topic))
        except Exception as e:
            logging.error(e)

    if do_finalize:
        logging.info ( "Finalized decode: %9.5f %s" % (confidence, hstr))

    return {'hstr': hstr, 'confidence': confidence}


if __name__ == '__main__':
    # commandline
    parser = OptionParser("usage: %prog [options] ")

    parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                       help="verbose output")

    parser.add_option ("-H", "--host", dest="host", type = "string", default=DEFAULT_HOST,
                       help="host, default: %s" % DEFAULT_HOST)

    parser.add_option ("-p", "--port", dest="port", type = "int", default=DEFAULT_PORT,
                       help="port, default: %d" % DEFAULT_PORT)

    parser.add_option ("-d", "--model-dir", dest="model_dir", type = "string", default=DEFAULT_MODEL_DIR,
                       help="kaldi model directory, default: %s" % DEFAULT_MODEL_DIR)

    parser.add_option ("-m", "--model", dest="model", type = "string", default=DEFAULT_MODEL,
                       help="kaldi model, default: %s" % DEFAULT_MODEL)

    (options, args) = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    kaldi_model_dir = options.model_dir
    kaldi_model     = options.model

    asr = ASR(engine = ASR_ENGINE_NNET3, model_dir = kaldi_model_dir,
          kaldi_beam = DEFAULT_BEAM, kaldi_acoustic_scale = DEFAULT_ACOUSTIC_SCALE,
          kaldi_frame_subsampling_factor = DEFAULT_FRAME_SUBSAMPLING_FACTOR)

    # run HTTP server
    #try:
   #     app.run(host="0.0.0.0", port=8080)
  #  except Exception as e:
   #     logging.error(e)
