import flair
import kafka
import logging
import json
from optparse import OptionParser

DEFAULT_TOPIC = "decoded_speech"
DEFAULT_BROKER = "localhost:9020"

parser.add_option ("-t", "--topic", dest="topic", type = "string", default=DEFAULT_TOPIC,
                    help="kafka topic, default: %d" % DEFAULT_TOPIC)

parser.add_option ("-b", "--broker", dest="broker", type = "string", default=DEFAULT_BROKER,
                    help="kafka broker, default: %d" % DEFAULT_BROKER)

(options, args) = parser.parse_args()


flair_sentiment = flair.models.TextClassifier.load('en-sentiment')
s = flair.data.Sentence("This is a test and I am not happy.")
flair_sentiment.predict(s)
total_sentiment = s.labels


logging.info('starting kafka consumer')
    consumer = kafka.KafkaConsumer(args.topic, bootstrap_servers=args.brokers)
    for msg in consumer:
        if exit_event.is_set():
            break
        try:
            last_data(json.loads(str(msg.value, 'utf-8')))
        except Exception as e:
            logging.error(e.message)
    logging.info('exiting kafka consumer')
