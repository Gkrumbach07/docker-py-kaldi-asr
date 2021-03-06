FROM quay.io/mpuels/docker-kaldi-asr:2018-06-21

ARG DIR_PKGCONFIG=/usr/lib/pkgconfig

ENV LD_LIBRARY_PATH /opt/kaldi/tools/openfst/lib:/opt/kaldi/src/lib

RUN mkdir -p ${DIR_PKGCONFIG}
COPY kaldi-asr.pc ${DIR_PKGCONFIG}

RUN apt-get install --no-install-recommends -y \
            libatlas-base-dev \
            pkg-config \
            python3-dev \
            python3-pip \
            python3-setuptools && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove -y

RUN pip3 install \
        cython==0.28.3 \
        numpy==1.14.4 \
        pathlib2==2.3.2 \
        plac==0.9.6 \
        python-json-logger==0.1.9 \
        setproctitle==1.1.10 \
        typing==3.6.4 \
        wheel \
        kafka \
        gunicorn \
        flask \
        Werkzeug==0.16.0

RUN pip3 install py-kaldi-asr==0.5.2

COPY app.py /opt/asr_server/
COPY wsgi.py /opt/asr_server/

RUN apt-get install xz-utils -y && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove -y

WORKDIR /opt/asr_server/
RUN wget https://raw.githubusercontent.com/gooofy/py-nltools/7b989dd4642317a2a0f402e94207ee3186385824/nltools/asr.py

ARG MODEL_NAME=kaldi-generic-en-tdnn_250-r20190609

WORKDIR /opt
RUN wget -q http://goofy.zamia.org/zamia-speech/asr-models/${MODEL_NAME}.tar.xz && \
    tar xf ${MODEL_NAME}.tar.xz && \
    mv ${MODEL_NAME} kaldi-model && \
    rm ${MODEL_NAME}.tar.xz

EXPOSE 8080

WORKDIR /opt/asr_server
CMD ["gunicorn"  , "--bind", "0.0.0.0:8080", "wsgi:app"]
