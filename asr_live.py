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
# very basic example client for our example speech asr server
#

import os
import sys
import logging
import traceback
import json
import wave
import struct
import requests

from time import time, sleep
from optparse import OptionParser

from vad import VAD
from pulserecorder import PulseRecorder


DEFAULT_URL      = 'localhost:8080'

DEFAULT_VOLUME                   = 150
DEFAULT_AGGRESSIVENESS           = 2

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


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)

source         = options.source
volume         = options.volume
aggressiveness = options.aggressiveness

url = 'http://%s/decode' % (options.host)

try:
    # pulseaudio recorder
    rec = PulseRecorder (source_name=source, volume=volume)

    rec.start_recording(frames_per_buffer=4000)
    print ("Please speak.")

except Exception as e:
    logging.critical(e)
    sys.exit(1)

try:
    longest_streak = 0
    last_phrase = ""
    while True:
        samples = rec.get_samples().tolist()

        finalize = False
        if longest_streak > 10:
            finalize = True


        data = {'audio'      : samples,
                'do_finalize': finalize}

        response = requests.post(url, data=json.dumps(data))
        if not response.ok:
            logging.error(response.text)
        else:
            if finalize:
                 logging.info ( "prediction    : %s - %f" % (response.json()['hstr'], response.json()['confidence']))
                 longest_streak = 0;
                 last_phrase = ""

            else:
                logging.info ( "prediction    : %s - %f" % (response.json()['hstr'], response.json()['confidence']))
                if(last_phrase == response.json()['hstr'] and response.json()['hstr'] != ""):
                    longest_streak += 1
                else:
                    longest_streak = 0
                    last_phrase = response.json()['hstr']

except KeyboardInterrupt:
    logging.info("Keyboard Interrupt: stopping service")
    rec.stop_recording()
