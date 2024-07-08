import ollama
import os
import shutil
import argparse
import sys

MIN_CHARS_IN_FILENAME = 30

ai_model_content_prompt = """
You are an expert author of stable diffusion prompts, Your output is the actual words of the 
prompt that will be used to generate the image. Use keywords or brief phrases separated by commas to describe the image.
Some words require emphasis, so use the following format:((word)) which will cause the model 
to focus on those keywords more.
"""


def describe_image(image_file_path):
    with open(image_file_path, 'rb') as file:
        response = ollama.chat(
            model='llava:34b',
            messages=[
                {
                    'role': 'system',
                    'content': ai_model_content_prompt
                },
                {
                    'role': 'user',
                    'content': 'Please describe this image in a manner suitable for use as a stable diffusion prompt',
                    'images': [file.read()],
                },
            ],
        )

    return response['message']['content']


if __name__ == '__main__':
    image_full_file_path = None
    if image_full_file_path is None:
        if len(sys.argv) > 1 and 'file_path=' in sys.argv[1]:
            parser = argparse.ArgumentParser()
            parser.add_argument('file_path', type=str, help='Path to the image to describe')
            args = parser.parse_args()
            if not args.file_path:
                image_full_file_path = input('Please provide a file path to the image you want to describe > ')
            else:
                image_full_file_path = args.file_path.replace('file_path=', '')
                if len(args.file_path) < MIN_CHARS_IN_FILENAME:
                    print('The file path provided is not valid')
                    exit(1)
        else:
            image_full_file_path = input('Please provide a file path to the image you want to describe > ')

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
