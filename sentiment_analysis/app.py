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
logging.basicConfig(level=logging.INFO)

flair_sentiment = flair.models.TextClassifier.load('en-sentiment')
s = flair.data.Sentence("This is a test and I am not happy.")
flair_sentiment.predict(s)
total_sentiment = s.labels


logging.info('starting kafka consumer')
    consumer = kafka.KafkaConsumer(args.topic, bootstrap_servers=args.brokers)
    for msg in consumer:
        try:
            message = json.loads(str(msg.value, 'utf-8'))
            if message == 'exit':
                break
            logging.info(message)
        except Exception as e:
            logging.error(e.message)
    logging.info('exiting kafka consumer')
