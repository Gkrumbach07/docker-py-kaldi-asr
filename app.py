import os
import logging
import json
from time import time, sleep
from collections import namedtuple
from optparse import OptionParser
from flask import Flask, request

from asr import ASR, ASR_ENGINE_NNET3
from kaldiasr.nnet3 import KaldiNNet3OnlineModel, KaldiNNet3OnlineDecoder
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
# states = None
producer = None
topic = None
asr = None


app = Flask(__name__)
# from werkzeug.contrib.profiler import ProfilerMiddleware
# app.config['PROFILE'] = True
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

# class DecoderState():
#     def __init__(self):
#         self.model = KaldiNNet3OnlineModel(kaldi_model_dir, kaldi_model)
#         self.decoder = KaldiNNet3OnlineDecoder(self.model)
#         self.last_used = time()



@app.route('/')
def info():
    return 'Use /decode to decode audio.'


@app.route('/decode', methods=['POST'])
def decode():
    try:
        audio       = request.json['audio']
        do_finalize = request.json['do_finalize']
        id          = request.json['id']
    except Exception as e:
        logging.error(e)
        return {'hstr': 'load error', 'confidence': 1}

    # set session state
    # if id not in states:
    #     states[id] = DecoderState()
    # else:
    #     states[id].last_used = time()

    hstr        = ''
    confidence  = 0.0

    # states[id].decoder.decode(SAMPLE_RATE, np.array(audio, dtype=np.float32), do_finalize)

    hstr, confidence = asr.decode(audio, do_finalize, stream_id=id)


    if do_finalize:
        # hstr, confidence = states[id].decoder.get_decoded_string()
        logging.debug ( "** %9.5f %s" % (confidence, hstr))

        # if done then remove state
        # states.pop(id)

        # if producing, then push to topic
        if producer != None:
            producer.send(topic, json.dumps(hstr).encode('utf-8'))
    # else:
        # hstr, confidence = states[id].decoder.get_decoded_string()

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

    # setup state memmory
    # states = {}

    #start producer
    broker = os.getenv('KAFKA_BROKER', None)
    topic = os.getenv('KAFKA_TOPIC', None)
    if topic != None and broker != None:
        producer = KafkaProducer(bootstrap_servers=broker)

    asr = ASR(engine = ASR_ENGINE_NNET3, model_dir = kaldi_model_dir,
          kaldi_beam = DEFAULT_BEAM, kaldi_acoustic_scale = DEFAULT_ACOUSTIC_SCALE,
          kaldi_frame_subsampling_factor = DEFAULT_FRAME_SUBSAMPLING_FACTOR)



    # run HTTP server
    try:
        # app.run(debug=True, host="0.0.0.0", port=8080)
        app.run(host="0.0.0.0", port=8080)
    except Exception as e:
        logging.error(e)
