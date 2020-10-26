import argparse
import logging
import os
import flair
from kafka import KafkaConsumer


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    return args


def main(args):
    flair_sentiment = flair.models.TextClassifier.load('en-sentiment')
    s = flair.data.Sentence("This is a test and I am not happy.")
    flair_sentiment.predict(s)
    total_sentiment = s.labels

    consumer = KafkaConsumer(args.topic, bootstrap_servers=args.brokers)
    for msg in consumer:
        out = msg.value if msg.value is not None else ""
        logging.info('received: ' + str(msg.value, 'utf-8'))
    logging.info('exiting')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting kafka-python-listener')
    parser = argparse.ArgumentParser(
            description='listen for some stuff on kafka')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='localhost:9092')
    parser.add_argument(
            '--topic',
            help='Topic to publish to, env variable KAFKA_TOPIC',
            default='bones-brigade')
    args = parse_args(parser)
    main(args)



# logging.info('starting kafka consumer')
#     consumer = kafka.KafkaConsumer(args.topic, bootstrap_servers=args.brokers)
#     while(True):
#         for msg in consumer:
#             try:
#                 message = json.loads(str(msg.value, 'utf-8'))
#                 if message == 'exit':
#                     break
#                 logging.info(message)
#             except Exception as e:
#                 logging.error(e.message)
#         logging.info('exiting kafka consumer')
