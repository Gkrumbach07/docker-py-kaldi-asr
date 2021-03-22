# Python Kaldi Live Audio Decoder API

This image contains Kaldi and
[py-kaldi-asr](https://github.com/gooofy/py-kaldi-asr), a simple Python
wrapper for Kaldi. It contains a Flask server in /opt/app that clients
can connect to to transcribe audio.

## What is in this repo
This repo contains a few elements:
- Audio decoder api
- Audio decoder client example
    - client simulator
    - live decoding interface
    - file decoding interface
- NLP notebook using Kafka

## Audio decoder api
This is a simple flask server that takes a POST request on the `/decode` route and returns a predicted result. This is meant to be used in
live decoding applications, so session states need to be saved. This API is not stateless, as it stores the state of the decoder in the server itself.
This is not a problem because later we will use OpenShift to deploy and scale the API properly.

### Deploying the api
First we can run the following commands to deploy the API and expose its route on OpenShift. The image already contains a pre trained model, but you can edit the Dockerfile and rebuild the image if you want to inject a different model. Currently this image relies on a community made image of Kaldi. 

Run these commands in the OpenShift CLI.
```
$ oc new-app \
  --docker-image=quay.io/gkrumbach07/docker-py-kaldi-asr:latest \
  --name=audio-decoder

$ oc expose service/audio-decoder
```
You can scale the number of pods as much as you want or you can set up a horizontal auto scaler in OpenShift.

### Setting up the client
To call the API service it is best to set up a client script which will automatically convert audio files / mic audio to raw vector data.
In this repo under the recorder folder, there is a client script that can be run to automate calling the API. You can run this script locally or as a service on OpenShift using the client simulator. 

If running locally, set up the pip environment with `pipenv install` in the `/recorder` subdirectory. There are three ways you can use this script.
- Live decoding
- Wav file decoding
- Simulating a client

#### Live decoding
For this option you need to first install pulseaudio. On Mac you can run the command `brew install pulseaudio`.
It is usually installed on most Linux distributions by default.

To run the live decoding session, first start up the pulseaudio server by running `pulseaudio` in a seperate terminal.
Then you can run the following command to start the session.
```
pipenv run python app.py -H {HOST}
```
The host is equal to the route you exposed from the decoder api above. You can specify other other options for the audio input but it is not needed.

#### Wav file decoding
This does not require pulseaudio, so all you need to run is:
```
pipenv run python app.py -H {HOST} -f {FILE}
```
There are sample files located in the `/data` folder.

#### Simulate a client (on OpenShift)
You can add the `-S` tag which will start a simulator. This picks a random wav file in the `/data` folder and decodes it. This repeats until the process is closed.
```
pipenv run python app.py -H {HOST} -S
```
If you plan to run the simulator on OpenShift, you will need to set the `DO_SIMULATE` enviroment variable to `True`. This makes it so the script will auto run as 
a simulator compared to the other options. You can deploy the script using OpenShift's source to image feature. Choose the from repository option and select Python as its base image. Make sure to also set the Context dir under Advanded options to `recorder`.

#### Kafka Streaming
You can stream your clients predictions to a Kafka topic using the tags `-b` for the broker and `-t` for the topic. In OpenShift, you can set the `KAFKA_BROKERS` and `KAFKA_TOPIC` enviroment variables to your desired Kafka streams. Using Kafka here will produce the decoded audio (text) and the user id to the desired Kafka topic.
```
pipenv run python app.py -H {HOST} -b {BROKER}:9092 -t {TOPIC}
```
Exmaples of how this stream is used can be found in the section on the sentiment analysis application below.

### Sentiment Analysis
The serice that this model runs on is just a jupyter notebook. It uses a couple pre trained models and should be used as a refrence on how you might integrate Kafka streaming into a model service. The notebook should run on a service that runs jupyter on Openshift ([service](https://github.com/jupyter/docker-stacks/tree/master/minimal-notebook)).

## Web App Dashboard
You run visualize the final output of this demo usng this [repo](https://github.com/Gkrumbach07/call_center_manage). Deploy this on Opneshift and make sure to set enviroment variables for Kafka support. All is outlined in the repo's readme.
