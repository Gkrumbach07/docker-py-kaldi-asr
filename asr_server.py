import os
import logging
import json
import _thread
from time import time, sleep
from collections import namedtuple
from optparse import OptionParser
from setproctitle import setproctitle
from flask import Flask, request

from kaldiasr.nnet3 import KaldiNNet3OnlineModel, KaldiNNet3OnlineDecoder
import numpy as np
from kafka import KafkaProducer

DEFAULT_HOST      = ''
DEFAULT_PORT      = 8080

DEFAULT_MODEL_DIR = '/opt/kaldi-model'
DEFAULT_MODEL     = 'model'

DEFAULT_VF_LOGIN  = 'anonymous'
DEFAULT_REC_DIR   = '/opt/data/recordings'
SAMPLE_RATE       = 16000

PROC_TITLE        = 'asr_server'

# globals
kaldi_model_dir = None
kaldi_model = None
states = None
producers = None

DecoderState = namedtuple('DecoderState',['decoder','last_used'])
ProducerState = namedtuple('ProducerState',['producer' 'client_id','last_used'])

app = Flask(__name__)


@app.route('/')
def info():
    return 'Use /decode to decode audio.'


@app.route('/decode', methods=['POST'])
def decode():
    try:
        audio       = request.form['audio']
        do_finalize = request.form['do_finalize']
        topic       = request.form['topic']
        broker      = request.form['broker']
        id          = request.form['id']

        logging.info(audio)

    except Exception as e:
        logging.error(e)

    # set session state
    if id not in states:
        states[id] = DecoderState(
            KaldiNNet3OnlineDecoder(KaldiNNet3OnlineModel(kaldi_model_dir, kaldi_model)),
            time())
    else:
        states[id] = states[id]._replace(last_used=time())

    # preform kafka setup
    if topic != None and broker != None:
        if broker not in producers:
            producers[broker] = ProducerState(
                KafkaProducer(bootstrap_servers=broker),
                id,
                time())
        else:
            producers[broker] = producers[broker]._replace(last_used=time())

    hstr        = ''
    confidence  = 0.0

    try:
        states[id].decoder.decode(SAMPLE_RATE, np.array(audio, dtype=np.float32), do_finalize)
    except Exception as e:
        logging.error("Decoder Error: " + str(e))

    if do_finalize:
        hstr, confidence = states[id].decoder.get_decoded_string()
        logging.debug ( "** %9.5f %s" % (confidence, hstr))

        # if producing, then push to topic
        if topic != None and broker != None:
            producers[broker].producer.send(topic, json.dumps(hstr).encode('utf-8'))

    hstr, confidence = states[id].decoder.get_decoded_string()

    return {'hstr': hstr, 'confidence': confidence}

def manage_states(delay, threadName):
   while True:
      sleep(delay)
      for key in states:
          if states[key].last_used > time() + delay:
              states.pop(key)
              logging.debug("Decoder '" + str(key) + "' was removed.")
      for key in producers:
          if producers[key].last_used > time() + delay:
              producers.pop(key)
              logging.debug("Producer '" + str(key) + "' was removed.")


def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


if __name__ == '__main__':

    setproctitle (PROC_TITLE)

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

    # setup memory
    states = {}
    producers = {}

    # start manage thread
    try:
        _thread.start_new_thread(manage_states, (600, "Thread1"))
        logging.info("Starting state manager thread.")
    except Exception as e:
        logging.error(e)

    # run HTTP server
    try:
        app.run(host="0.0.0.0", port=8080)
    except Exception as e:
        logging.error(e)
