
#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright 2017 Guenter Bartsch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# simple speech recognition http api server
#
# WARNING:
#     right now, this supports a single client only - needs a lot more work
#     to become (at least somewhat) scalable



import os
import sys
import logging
import traceback
import json
import datetime
import wave
import errno
import struct

from time import time
from optparse import OptionParser
from setproctitle import setproctitle
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

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

#
# globals
#
kaldi_model_dir = None
kaldi_model = None
states = None

class SessionState():
    def __init__(self):
        nnet3_model = KaldiNNet3OnlineModel (kaldi_model_dir, kaldi_model)
        self.decoder = KaldiNNet3OnlineDecoder(nnet3_model)
        self.current_broker = None
        self.current_topic = None
        self.producer = None

    def updateProducer(self, new_broker, new_topic):
        if self.current_broker != new_broker:
            logging.info('Creating new Kafka producer\
             %s with topic %s' % (new_broker, new_topic))

            self.current_broker = new_broker
            self.current_topic = new_topic
            if self.producer != None:
                self.producer.close()
            self.producer = KafkaProducer(bootstrap_servers=self.current_broker)

        elif self.current_topic != new_topic:
            logging.info('Changing the Kafka topic to %s', new_topic)
            self.current_topic = new_topic




def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

class SpeechHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        logging.debug("GET")
        self.send_error(400, 'Invalid request')

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        if self.path=="/decode":

            data = json.loads(self.rfile.read(int(self.headers.getheader('content-length'))))

            # set vars
            audio       = data['audio']
            do_finalize = data['do_finalize']
            topic       = data['topic']
            broker      = data['broker']
            id          = data['id']

            # set session state
            if id not in states:
                states[id] = SessionState()
            state = states[id]

            # preform kafka setup
            do_produce = topic != None and broker != None
            if do_produce:
                state.updateProducer(broker, topic)

            hstr        = ''
            confidence  = 0.0

            state.decoder.decode(SAMPLE_RATE, np.array(audio, dtype=np.float32), do_finalize)

            if do_finalize:

                hstr, confidence = state.decoder.get_decoded_string()

                logging.debug ( "*****************************************************************************")
                logging.debug ( "**")
                logging.debug ( "** %9.5f %s" % (confidence, hstr))
                logging.debug ( "**")
                logging.debug ( "*****************************************************************************")

                # remove decoder from memory
                states.pop(id)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            hstr, confidence = decoder.get_decoded_string()

            if do_produce:
                state.producer.send(state.current_topic, json.dumps(hstr).encode('utf-8'))

            reply = {'hstr': hstr, 'confidence': confidence}

            self.wfile.write(json.dumps(reply))
            return


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

    # run HTTP server
    try:
        server = HTTPServer((options.host, options.port), SpeechHandler)
        logging.info('listening for HTTP requests on %s:%d' % (options.host, options.port))

        # wait forever for incoming http requests
        server.serve_forever()

    except KeyboardInterrupt:
        logging.error('^C received, shutting down the web server')
        server.socket.close()
