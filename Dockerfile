FROM debian:8

ARG MAKE_JOBS=1

RUN apt-get update && apt-get install --no-install-recommends -y  \
    autoconf \
    automake \
    bzip2 \
    g++ \
    git \
    libatlas3-base \
    libtool-bin \
    make \
    patch \
    python2.7 \
    python3 \
    python-pip \
    subversion \
    wget \
    zlib1g-dev && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove -y

RUN mkdir -p /opt/kaldi && \
    git clone https://github.com/kaldi-asr/kaldi /opt/kaldi && \
    cd /opt/kaldi/tools && \
    make -j${MAKE_JOBS} && \
    ./install_portaudio.sh && \
    cd /opt/kaldi/src && \
    ./configure --shared && \
    sed -i '/-g # -O0 -DKALDI_PARANOID/c\-O3 -DNDEBUG' kaldi.mk && \
    make -j${MAKE_JOBS} depend && \
    make -j${MAKE_JOBS} checkversion && \
    make -j${MAKE_JOBS} kaldi.mk && \
    make -j${MAKE_JOBS} mklibdir && \
    make -j${MAKE_JOBS} \
	base \
	decoder \
	fstext \
	nnet3 \
	online2 \
	util && \
    cd /opt/kaldi && git log -n1 > current-git-commit.txt && \
    rm -rf /opt/kaldi/.git && \
    rm -rf /opt/kaldi/egs/ /opt/kaldi/windows/ /opt/kaldi/misc/ && \
    find /opt/kaldi/src/ \
	 -type f \
	 -not -name '*.h' \
	 -not -name '*.so' \
	 -delete && \
    find /opt/kaldi/tools/ \
	 -type f \
	 -not -name '*.h' \
	 -not -name '*.so' \
	 -not -name '*.so*' \
	 -delete
             
ARG DIR_PKGCONFIG=/usr/lib/pkgconfig

ENV LD_LIBRARY_PATH /opt/kaldi/tools/openfst/lib:/opt/kaldi/src/lib

RUN mkdir -p ${DIR_PKGCONFIG}
COPY kaldi-asr.pc ${DIR_PKGCONFIG}

RUN apt-get install --no-install-recommends -y \
            libatlas-base-dev \
            pkg-config \
            python-dev && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove -y

RUN pip install \
        cython==0.28.3 \
        numpy==1.14.4 \
        pathlib2==2.3.2 \
        plac==0.9.6 \
        python-json-logger==0.1.9 \
        setproctitle==1.1.10 \
        typing==3.6.4 \
        kafka

RUN pip install py-kaldi-asr==0.4.1

COPY asr_server.py /opt/asr_server/

RUN apt-get install xz-utils -y && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove -y

ARG MODEL_NAME=kaldi-generic-en-tdnn_250-r20190609

WORKDIR /opt
RUN wget -q http://goofy.zamia.org/zamia-speech/asr-models/${MODEL_NAME}.tar.xz && \
    tar xf ${MODEL_NAME}.tar.xz && \
    mv ${MODEL_NAME} kaldi-model && \
    rm ${MODEL_NAME}.tar.xz

EXPOSE 8080

WORKDIR /opt/asr_server
CMD ["python", "asr_server.py"]
