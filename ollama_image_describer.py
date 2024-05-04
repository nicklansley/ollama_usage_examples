import ollama
import os
import shutil
import argparse

MIN_CHARS_IN_FILENAME = 30

ai_model_content_prompt = """
Please describe this image in a way that could be used to generate it using a text-to-image model.
You are welcome to provide negative prompt words to help tune the image.
"""

def describe_image(image_file_path):
    with open(image_file_path, 'rb') as file:
        response = ollama.chat(
            model='llava:34b',
            messages=[
                {
                    'role': 'user',
                    'content': ai_model_content_prompt,
                    'images': [file.read()],
                },
            ],
        )

    return response['message']['content']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file_path', type=str, help='Path to the image to describe')
    args = parser.parse_args()
    image_full_file_path = args.file_path.replace('file_path=', '')

    try:
        print('Ollama Image Describer describing this image file:', image_full_file_path)

        print('Processing', image_full_file_path, '...')

        description = describe_image(image_full_file_path)
        print('Description:', description)

        print('Ollama Image Describer finished')

    except KeyboardInterrupt:
        print('Ollama Image Describer finished due to keyboard interrupt')

    except Exception as e:
        print('Error:', e)
        print('Ollama Image Describer finished with errors')
