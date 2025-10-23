### 

First Test:

```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "generate_function",
    "language": "Python",
    "task": "sort a list of integers"
  }'
```
