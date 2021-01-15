#!/bin/bash

BROKER=odh-message-bus-kafka-brokers

oc new-project audio-decoder-demo
oc project audio-decoder-demo

# kafka consumer for decoded speech -> pushes data through sentiment analysis
# oc new-app registry.access.redhat.com/ubi8/python-36~https://github.com/Gkrumbach07/docker-py-kaldi-asr.git \
#   -e KAFKA_BROKERS=$BROKER:9092 \
#   -e KAFKA_TOPIC=decoded-speech \
#   --name=sentiment-consumer \
#   --context-dir=sentiment_analysis
#
# oc expose service/sentiment-consumer

# audio decoder multi user api
oc new-app \
  --docker-image=quay.io/gkrumbach07/docker-py-kaldi-asr:latest \
  --name=audio-decoder

oc expose service/audio-decoder

HOST=$(oc get routes/audio-decoder -o jsonpath='{ .status.ingress[0].routerCanonicalHostname }')

# change to use multi user


oc new-app registry.access.redhat.com/ubi8/python-36~https://github.com/Gkrumbach07/docker-py-kaldi-asr.git \
  -e KAFKA_BROKERS=$BROKER:9092 \
  -e KAFKA_TOPIC=decoded-speech \
  -e HOST=$HOST \
  -e DO_SIMULATE=True \
  --name=call-simulator \
  --context-dir=recorder


oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyter-notebooks/master/image-streams/s2i-minimal-notebook.json
oc new-app s2i-minimal-notebook:3.6 --name minimal-notebook
oc expose svc/minimal-notebook
