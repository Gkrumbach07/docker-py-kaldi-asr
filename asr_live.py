import os
import sys
import logging
import traceback
import json
import wave
import struct
import requests
import random

from time import time, sleep
from optparse import OptionParser

from pulserecorder import PulseRecorder


DEFAULT_URL = 'localhost:8080'

DEFAULT_VOLUME = 150

#
# commandline
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                    help="verbose output")

parser.add_option ("-H", "--host", dest="host", type = "string", default=DEFAULT_URL,
                    help="host, default: %s" % DEFAULT_URL)

parser.add_option ("-V", "--volume", dest="volume", type = "int", default=DEFAULT_VOLUME,
                    help="broker port, default: %d" % DEFAULT_VOLUME)

parser.add_option ("-s", "--source", dest="source", type = "string", default=None,
                    help="pulseaudio source, default: auto-detect mic")

parser.add_option('-b', '--broker', dest="broker", type = "string", help='The bootstrap servers')

parser.add_option('-t', '--topic', dest="topic", type = "string", help='Topic to publish to')


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)

source         = options.source
volume         = options.volume

topic = None
broker = None
if options.topic and options.broker:
    topic = options.topic
    broker = options.broker
elif (options.topic or options.broker) and  not (options.topic and options.broker):
    logging.warning("A topic and broker need to be specified. Kafka is diabled")

url = 'http://%s/decode' % (options.host)

try:
    # pulseaudio recorder
    rec = PulseRecorder (source_name=source, volume=volume)

    rec.start_recording(frames_per_buffer=100)
    print ("Please speak.")

except Exception as e:
    logging.critical(e)
    sys.exit(1)

try:
    longest_streak = 0
    last_phrase = ""
    id = random.randint(0, 99999)

    while True:
        samples = rec.get_samples().tolist()

        finalize = False
        if longest_streak > 3:
            finalize = True

        data = {'audio'      : samples,
                'do_finalize': finalize,
                'topic'      : topic,
                'broker'     : broker,
                'id'         : id}

        response = requests.post(url, json=data)
        if not response.ok:
            logging.error(response.text)
        else:
            if finalize:
                 logging.info ( "\tFinal    : %s - %f" % (response.json()['hstr'], response.json()['confidence']))
                 longest_streak = 0;
                 last_phrase = ""

            else:
                logging.info ( "\tPrediction    : %s - %f" % (response.json()['hstr'], response.json()['confidence']))
                if(last_phrase == response.json()['hstr'] and response.json()['hstr'] != ""):
                    longest_streak += 1
                else:
                    longest_streak = 0
                    last_phrase = response.json()['hstr']

except KeyboardInterrupt:
    logging.info("Keyboard Interrupt: stopping service")
    rec.stop_recording()
