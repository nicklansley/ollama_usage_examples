from dotenv import load_dotenv
import ollama
import os

load_dotenv()

NUM_CTX = int(os.getenv("NUM_CTX", "8000"))
summarising_ai_model = os.getenv("SUMMARISING_AI_MODEL", 'llama3.1:latest')

ai_prompt_convert_html_to_plain_text = """
You are an expert at converting HTML content to plain text. There is no need to retain any formatting or links,
just return the plain text content. The user will provide you with an HTML message to convert.
"""

def call_ai_model(model, prompt, user_content):
    response = ollama.chat(
        model=model, options={"num_ctx": NUM_CTX},
        messages=[
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': user_content},
        ])

    return response['message']['content'].strip()


def ai_convert_html_to_plain_text(html_source: str) -> str:
    plain_text = call_ai_model(summarising_ai_model, ai_prompt_convert_html_to_plain_text, html_source)
    return plain_text.replace('\n', '. ').replace('..', '.').strip()


if __name__ == "__main__":
    print('Converting HTML to plain text using AI')
    html_file = input('Enter a filepath to an HTML document > ')
    with open(html_file, 'r') as f:
        html_lines = f.readlines()
        html = ''
        for line in html_lines:
            html += line

    plain_text = ai_convert_html_to_plain_text(html)
    print(plain_text)