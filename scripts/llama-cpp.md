## USE llama.cpp

clone the code

```bash
git clone https://github.com/ggerganov/llama.cpp
```


### llama.cpp build
```
mkdir build && cd build
sudo apt install libcurl4-openssl-dev
cmake .. -B llama.cpp/build \
    -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=ON -DLLAMA_CURL=ON
cmake --build . --clean-first --config Release -j$(nproc)

###
cmake .. -B llama.cpp/build \
    -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=ON -DLLAMA_CURL=ON

cmake --build . --config Release -j --clean-first --target llama-cli llama-gguf-split


```


### get Qwen3-30B-A3B-Thinking-2507-GGUF

```
 wget https://huggingface.co/unsloth/Qwen3-30B-A3B-Thinking-2507-GGUF/resolve/main/Qwen3-30B-A3B-Thinking-2507-Q8_0.gguf
```


### run the server

```bash
./bin/llama-server -m ~/models/Qwen3-30B-A3B-Thinking-2507-Q8_0.gguf   --host 0.0.0.0   --port 8080   -ngl 999   -c 32768   -r 1.3   --temp 0.8
```

### run web broswer to test the model

```web
http://localhost:8080/
```

### run gpt-oss-120-mxfp4

```bash
!/usr/bin/env bash
MODEL=~/models/gpt-oss-120b-mxfp4-00001-of-00003.gguf

./bin/llama-server \
    -m "$MODEL" \
    --host 0.0.0.0 \
    --port 8080 \
    -ngl 40 \
    -c 65535 \
    -b 1 \
    -t 8 \
    --temp 0.7 \
    --mlock \
    --jinja \
    --no-mmap
```

### watch

```
 watch -n1 'ps -o pid,pmem,rss,vsz,cmd -p $(pgrep llama-server)'
```