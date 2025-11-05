# Dockerfile to build mk270/whitakers-words and produce a 'words' binary
FROM ubuntu:22.04

# install build tools and GNAT (Ada) + gprbuild
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
       git build-essential gnat gprbuild make ca-certificates wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# clone the mk270 repo
RUN git clone https://github.com/mk270/whitakers-words.git

WORKDIR /opt/whitakers-words

# Some build reports recommend adjusting the Makefile options (ensure capital J).
# If the Makefile already contains the right line the sed will leave it as-is.
RUN sed -i 's/^GPRBUILD_OPTIONS .*$/GPRBUILD_OPTIONS := -j4 -gnatwJ/' Makefile || true

# Build. 'make' should create bin/words (or similar) per the project structure.
RUN make

# show artifact
RUN ls -la bin || true

# keep the built binary in /opt/whitakers-words/bin
# default container entrypoint: show version/help of the binary
ENTRYPOINT ["/bin/bash","-lc","/opt/whitakers-words/bin/words --help || echo 'words binary built (or check /opt/whitakers-words/bin)'; sleep 3600"]

