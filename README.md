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
This is a simple flask server that takes a POST request on the `/decode` route and returns a predicted result. This is meant to be used in
live decoding applications, so session states need to be saved. This API is not stateless, as it stores the state of the decoder in the server itself.
This is not a problem because later we will use OpenShit to deploy and scale the API properly.

## Deploying the api
First we can run the following commands to deploy the API and expose its route.
```
$ oc new-app \
  --docker-image=quay.io/gkrumbach07/docker-py-kaldi-asr:latest \
  --name=audio-decoder

$ oc expose service/audio-decoder
```
Now we need to change the routes load balancer so the API will scale properly. After exposing the route,
navigate to the routes yaml and insert the following.
```
apiVersion: v1
kind: Route
metadata:
  annotations:
    haproxy.router.openshift.io/balance: source
[...]
```
Setting the load balancer to `source` makes it so clients will always hit the same API container based on the hash of their IP address. This ensures the client's state is not lost after numerous calls to the API.

## Setting up the client
To call the API service it is best to set up a client script which will automatically convert audio files / mic audio to raw vector data. 
