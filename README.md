# Python Kaldi Audio Decoder API

This image contains Kaldi and
[py-kaldi-asr](https://github.com/gooofy/py-kaldi-asr), a simple Python
wrapper for Kaldi. It contains a Flask server in /opt/asr_server that clients
can connect to to transcribe audio.

## What is in this repo
This repo contains a few elements:
- Audio decoder api
- Audio decoder client example
-- client simulator
-- live decoding interface
-- file decoding interface
