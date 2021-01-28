# Python Kaldi Live Audio Decoder API

This image contains Kaldi and
[py-kaldi-asr](https://github.com/gooofy/py-kaldi-asr), a simple Python
wrapper for Kaldi. It contains a Flask server in /opt/asr_server that clients
can connect to to transcribe audio.

## What is in this repo
This repo contains a few elements:
- Audio decoder api
- Audio decoder client example
    - client simulator
    - live decoding interface
    - file decoding interface

### Audio decoder api
This is a simple flask server that takes a POST request on the `/decode` route and returns a predicted result. This meant to be used in
live decoding so session states are saved. This API is not stateless, as it stores the state of the decoder in the server itself.
This is not a problem because later we will use OpenShit to deploy and scale the api properly.

