## USE llama.cpp

clone the code

```bash
git clone https://github.com/ggerganov/llama.cpp
```


### llama.cpp build
```
mkdir build && cd build
sudo apt install libcurl4-openssl-dev
cmake .. -DLLAMA_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j$(nproc)
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