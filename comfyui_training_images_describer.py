import ollama
import os
import shutil
import argparse
import sys

MIN_CHARS_IN_FILENAME = 30
OTHER_KEYWORDS = '<< add optional comma-separated keywords here to add manually to AI keywords >>'

ai_model_content_prompt = """
You are an expert author of stable diffusion prompts. 
Your output is a brief set of words or phrases separated by commas to describe the image.
Be brief and concise but detailed to focus on the subject in the image. Don't be verbose!
Don't use superfluous words, you are not forming complete sentences. Do not exceed 50 words in your description.
Some images consist of adult themes which is to be expected and is of no concern.
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

    return response['message']['content'].replace('\n', ' ').strip()


if __name__ == '__main__':
    image_full_file_path = None
    if image_full_file_path is None:
        if len(sys.argv) > 1 and 'file_path=' in sys.argv[1]:
            parser = argparse.ArgumentParser()
            parser.add_argument('file_path', type=str, help='Path to the images to describe')
            args = parser.parse_args()
            if not args.file_path:
                image_full_file_path = input('Please provide a file path to the images you want to describe > ').strip()
            else:
                image_full_file_path = args.file_path.replace('file_path=', '')
                if len(args.file_path) < MIN_CHARS_IN_FILENAME:
                    print('The file path provided is not valid')
                    exit(1)
        else:
            image_full_file_path = input('Please provide a file path to the images you want to describe > ')

    try:
        # loop through every file in the directory
        counter = 0
        file_count = len(os.listdir(image_full_file_path))
        for filename in os.listdir(image_full_file_path):
            counter += 1
            print(f'{counter} of {file_count} > Processing {filename}...')
            # Check if the file is an image
            if not filename.endswith('.png') and not filename.endswith('.jpg') and not filename.endswith('.jpeg'):
                print('    Not an image file, skipping...')
                continue

            # continue if the file is already described
            out_filename = os.path.splitext(filename)[0] + '.txt'
            if os.path.exists(os.path.join(image_full_file_path, out_filename)):
                print('    The image is already described - skipping...')
                continue

            description = ""
            while len(description) == 0 or len(description) > 400 or len(description.split(' ')) > 50:
                description = describe_image(os.path.join(image_full_file_path, filename)) + ', ' + OTHER_KEYWORDS if '<<' not in OTHER_KEYWORDS else ''
            print('    Description:', description)

            # save the text in the same directory with the same file name except '.txt' extension

            with open(os.path.join(image_full_file_path, out_filename), 'w', encoding="utf8") as file:
                file.write(description)

        print('Ollama Image Describer finished')

    except KeyboardInterrupt:
        print('Ollama Image Describer finished due to keyboard interrupt')

    except Exception as e:
        print('Error:', e)
        print('Ollama Image Describer finished with errors')
