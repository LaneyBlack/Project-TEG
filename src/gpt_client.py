import os
import openai
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv


class GPTClient:
    def __init__(self, model="gpt-4o-mini"):
        env_path = os.path.join("", ".env")
        load_dotenv(env_path)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.chat = ChatOpenAI(
            model=model,
            temperature=0.9
        )

    def get_openai_response(self, prompt, max_tokens=100):
        try:
            123
        except Exception as e:
            print('Error', e)


    def ask(self, prompt, max_tokens=100):
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    # Replace with your actual API key
    client = GPTClient()

    while True:
        prompt = input("You: ")
        if prompt.lower() in ["exit", "quit"]:
            break
        response = client.ask(prompt)
        print("GPT:", response)
