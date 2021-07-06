import kafka
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import json
import os

def main():
    brokers = 'odh-message-bus-kafka-bootstrap.opf-kafka.svc:9092'
    from_topic = 'audio-decoder.decoded-speech'
    to_topic = 'audio-decoder.sentiment-text'
    ssl_cert_path = os.getenv("SSL_CERT_PATH", None)

    consumer = kafka.KafkaConsumer(from_topic, bootstrap_servers=brokers, group_id="default", security_protocol="SSL", ssl_cafile=ssl_cert_path + "/ca.crt", ssl_keyfile=ssl_cert_path + "/user.key", ssl_password=ssl_cert_path + "/user.password", ssl_certfile=ssl_cert_path + "/user.crt")
    producer = kafka.KafkaProducer(bootstrap_servers=brokers, security_protocol="SSL", ssl_cafile=ssl_cert_path + "/ca.crt", ssl_keyfile=ssl_cert_path + "/user.key", ssl_password=ssl_cert_path + "/user.password", ssl_certfile=ssl_cert_path + "/user.crt")
    
    nltk.download('vader_lexicon')
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')

    # change the consumer_id to any string
    consumer_id = "DEFAULT"
    
    # nltk sentiment
    sid = SentimentIntensityAnalyzer()

    print("ready to consume")
    for msg in consumer:
        if msg.value is not None:
            # first we will load in the json object
            obj_in = json.loads(msg.value.decode('utf-8'))

            if obj_in["sentence"] == "":
                continue

            # Using nltk, we create a sentence and predict its sentiment.
            quality = sid.polarity_scores(obj_in["sentence"])

            # Using NLTK, we tokenize the sentence and extract only the nouns
            text = nltk.word_tokenize(obj_in["sentence"])
            tokens = nltk.pos_tag(text)
            nouns = []
            for pair in tokens:
                if pair[1][:2] == 'NN':
                    nouns.append(pair[0])
                    
            # We complile our model outputs into an object with an ID.
            # We use an ID to track which call this text came from
            data = {
                "sentence": obj_in["sentence"],
                "quality": quality['compound'],
                "nouns": nouns,
                "id": obj_in["id"],
                "consumer": consumer_id
            }

            # Now we can send this data out to our to_topic, so it
            # can be recived by our web application
            producer.send(to_topic, json.dumps(data).encode('utf-8'))

    print('exiting')

if __name__ == '__main__':
    main()
