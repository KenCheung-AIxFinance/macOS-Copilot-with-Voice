from openai import OpenAI

API_KEY = 'sk-1b53c98a3b8c4abcaa1f68540ab3252d'

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello, I am Ken"},
        {"role": "user", "content": "現在幾點啊"},
    ],
    stream=False
)

print(response.choices[0].message.content)