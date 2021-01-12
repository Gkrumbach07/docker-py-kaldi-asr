import os
import sys
import logging
import traceback
import json
import wave
import struct
import requests
import random
import socket

from time import time, sleep
from optparse import OptionParser

from pulserecorder import PulseRecorder
from vad import VAD, BUFFER_DURATION


DEFAULT_URL = 'localhost:8080'
DEFAULT_VOLUME = 150
DEFAULT_AGGRESSIVENESS = 2
stream_id = "__defualt__"

def get_uuid():
    ip = None
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        logging.warning("Could not get ip address for uuid, defaulting to random number.")
        ip = random.randint(0,99999)

    t = time()
    return int(hash(str(ip) + str(t)))


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') != '' else default


def simulate(url, topic, broker):
    # pick audio file and decode
    while(True):
        file = random.choice(os.listdir("data"))
        decode_wav_file("data/" + file, url, topic, broker)
        sleep(5 * 60)


def decode_wav_file(file, url, topic, broker):
    global stream_id

    logging.info('decoding %s...' % file)
    wavf = wave.open(file, 'rb')

    # check format
    assert wavf.getnchannels()==1
    assert wavf.getsampwidth()==2

    # process file in 250ms chunks

    chunk_frames = 250 * wavf.getframerate() / 1000
    tot_frames   = wavf.getnframes()

    num_frames = 0
    while num_frames < tot_frames:

        finalize = False
        if (num_frames + chunk_frames) < tot_frames:
            nframes = chunk_frames
        else:
            nframes = tot_frames - num_frames
            finalize = True

        frames = wavf.readframes(int(nframes))
        num_frames += nframes
        samples = struct.unpack_from('<%dh' % nframes, frames)


        data = {'audio'      : list(samples),
                'do_finalize': finalize,
                'topic'      : topic,
                'broker'     : broker,
                'id'         : stream_id}


        response = requests.post(url, json=data)

        if not response.ok:
            logging.error(response.text)
        elif finalize:
            logging.info("Decoding finished for " + file)
            logging.info("Prediction    : %s - %f" % (response.json()['hstr'], response.json()['confidence']))
        else:
            logging.debug("Prediction    : %s - %f" % (response.json()['hstr'], response.json()['confidence']))

    wavf.close()


def decode_live(source, volume, aggressiveness, url, topic, broker):
    global stream_id
    try:
        # pulseaudio recorder
        rec = PulseRecorder (source_name=source, volume=volume)
        vad = VAD(aggressiveness=aggressiveness)

        rec.start_recording()
        logging.info("Start talking.")

        while True:
            samples = rec.get_samples()
            audio, finalize = vad.process_audio(samples)

            if not audio:
                continue

            data = {'audio'      : audio,
                    'do_finalize': finalize,
                    'topic'      : topic,
                    'broker'     : broker,
                    'id'         : stream_id}

            response = requests.post(url, json=data)
            if not response.ok:
                logging.error(response.text)
            else:
                logging.info ( "\tPrediction    : %s - %f" % (response.json()['hstr'], response.json()['confidence']))
    except KeyboardInterrupt:
        logging.info("Keyboard Interrupt: stopping service")
        rec.stop_recording()
    except Exception as e:
        logging.critical(e)
        sys.exit(1)


def main(options):
    # enable logging
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)


    # set args to vars
    source         = options.source
    volume         = options.volume
    aggressiveness = options.aggressiveness
    url = 'http://%s/decode' % (get_arg('HOST', options.host))

    # for simulations, set if simulator should be used
    do_simulate = get_arg('DO_SIMULATE', False)

    # kafka streaming
    broker = get_arg('KAFKA_BROKERS', options.broker)
    topic = get_arg('KAFKA_TOPIC', options.topic)
    if options.topic and options.broker:
        topic = options.topic
        broker = options.broker
        logging.info("Kafka broker and topic are set.")
    else:
        logging.warning("A topic and broker were not specified. Kafka is diabled")


    # set session id
    stream_id = get_uuid()


    # function of script
    if options.file:
        decode_wav_file(options.file, url, topic, broker)
    elif do_simulate:
        simulate(url, topic, broker)
    else:
        decode_live(source, volume, aggressiveness, url, topic, broker)


if __name__ == '__main__':
    # parse args
    parser = OptionParser("usage: %prog [options]")

    parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                        help="verbose output")

    parser.add_option ("-H", "--host", dest="host", type = "string", default=DEFAULT_URL,
                        help="host, default: %s" % DEFAULT_URL)

    parser.add_option ("-V", "--volume", dest="volume", type = "int", default=DEFAULT_VOLUME,
                        help="broker port, default: %d" % DEFAULT_VOLUME)

    parser.add_option ("-a", "--aggressiveness", dest="aggressiveness", type = "int", default=DEFAULT_AGGRESSIVENESS,
                       help="VAD aggressiveness, default: %d" % DEFAULT_AGGRESSIVENESS)

    parser.add_option ("-s", "--source", dest="source", type = "string", default=None,
                        help="pulseaudio source, default: auto-detect mic")

    parser.add_option ("-f", "--file", dest="file", type = "string", default=None,
                        help="wave file, default: no file; use live decoding")

    parser.add_option('-b', '--broker', dest="broker", type = "string", help='The bootstrap servers')

    parser.add_option('-t', '--topic', dest="topic", type = "string", help='Topic to publish to')

    (options, args) = parser.parse_args()
    main(options)