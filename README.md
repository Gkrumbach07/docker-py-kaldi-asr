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
In this repo under the recorder folder, there is a client script that cane be run to automate calling the API.

Set up the pip environment with `pipenv install` in the `/recorder` subdirectory. There are three ways you can use this script.
- Live decoding
- Wav file decoding
- Simulating a client

### Live decoding
For this option you need to first install pulseaudio. On Mac you can run the command `brew install pulseaudio`.
It is usually installed on most Linux distributions by default.

To run the live decoding session, first start up the pulseaudio server by running `pulseaudio` in a seperate terminal.
Then you can run the following command to start the session.
```
pipenv run python app.py -H {HOST}
```
The host is equal to the route you exposed from the decoder above.

### Wav file decoding
This does not requre pulseaudio, so all you need to run is:
```
pipenv run python app.py -H {HOST} -f {FILE}
```
There are sample files located in the `/data` folder.

NOTE: The wave files must have a sample rate of 16 kHz. This can be changed in the decoder itself if need be.

### Simulate a client
You can add the `-S` tag which will start a simulator. This picks a random wav file in the `/data` folder and decodes it. This repeats until the process is closed.
```
pipenv run python app.py -H {HOST} -S
```
### Kafka Streaming
You can stream your clients predictions to a Kafka topic using the tags `-b` for the broker and `-t` for the topic. 
```
pipenv run python app.py -H {HOST} -b {BROKER}:9092 -t {TOPIC}
```
Exmaples of how this stream is used can be found in the section on the sentiment analysis application below.
