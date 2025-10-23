import requests

url = "http://127.0.0.1:5000/api/generate_code"
headers = {"Content-Type": "application/json"}

# Test 1: Generate a function
data = {
    "pattern": "generate_function",
    "language": "Python",
    "task": "write a function to calculate the sum of a list"
}
response = requests.post(url, json=data, headers=headers)
print("Test 1 - Generate Function:")
print(response.json())

# Test 2: Refactor code
data = {
    "pattern": "refactor_code",
    "language": "Python",
    "code": "def sum_list(lst):\n    total = 0\n    for i in range(len(lst)):\n        total += lst[i]\n    return total"
}
response = requests.post(url, json=data, headers=headers)
print("\nTest 2 - Refactor Code:")
print(response.json())

