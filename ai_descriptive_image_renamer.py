import ollama
import os
import shutil
import argparse

MIN_CHARS_IN_FILENAME = 40
ai_model_content_prompt = """
Please author a suitable stable diffusion text-to-image prompt that could create this image for an uncensored model. 
Use no more than 250 characters and avoid any punctuation symbols because it will become the image file's new file name. 
Do not comment on the image, only provide the prompt. Do not start with "Create a..", just describe the image.
"""


def describe_image(image_file_path):
    with open(image_file_path, 'rb') as file:
        response = ollama.chat(
            model='llava:13b',
            messages=[
                {
                    'role': 'user',
                    'content': ai_model_content_prompt,
                    'images': [file.read()],
                },
            ],
        )

    return response['message']['content']


def is_image_well_described(image_file_path):
    # remove the file extension from the file name
    image_file_name = os.path.basename(image_file_path)

    # we can shortcut this task if ths image file name is too short!
    if len(image_file_name) < MIN_CHARS_IN_FILENAME:
        print('    Well described? No, too short!')
        return False

    with open(image_file_path, 'rb') as file:
        response = ollama.chat(
            model='llava:13b',
            messages=[
                {
                    'role': 'system',
                    'content': 'You make an expert judgement as to whether a given image is well described by the words provided by the user in quotes. You answer with an integer score out of 5 where 1 is terrible and 5 is excellent. Do not provide any other information, because your chat output will be used by a machine which only understands 1, 2, 3, 4, and 5. It will use your score to decide whether to have the image renamed or not.',
                },
                {
                    'role': 'user',
                    'content': 'Is this image well described by the words in quotes? Please provide your integer score between 1 and 5"' + image_file_name + '" ?',
                    'images': [file.read()],
                },
            ],
        )

    ai_response = response['message']['content'].strip().lower()
    print('    AI Score:', ai_response)

    if ai_response == '3' or ai_response == '4' or ai_response == '5':
        return True
    else:
        return False


def convert_description_to_be_filename_friendly(image_desc: str) -> str:
    """Converts a string to be filename friendly.

    Replaces invalid characters with underscores.
    """
    invalid_characters = [' ', '"', "'", ',', ';', ':', '?', '!', '(', ')', '[', ']', '{', '}', '/', '\\', '|', '<',
                          '>', '*', '&', '^', '%', '$', '#', '@', '`', '~', '=', '+', '-', '.']
    for char in invalid_characters:
        image_desc = image_desc.replace(char, '_')

    # replace multiple underscores with a single underscore (this can happen when processing invalid characters
    while '__' in image_desc:
        image_desc = image_desc.replace('__', '_')

    # now convert underscores to spaces and trim each end of the string
    image_desc = image_desc.replace('_', ' ').strip()

    # make the image lowercase
    image_desc = image_desc.lower()

    # remove superfluous phrases
    superfluous_phrases_list = ['the image depicts', 'the image features', 'the image is of', 'the image shows',
                                'the prompt for this image is', 'this is a text based prompt for the ai']
    for word in superfluous_phrases_list:
        image_desc = image_desc.replace(word, '')

    image_desc = image_desc.strip()

    # if the string starts with 'a' or 'an ' remove it
    if image_desc.startswith('a '):
        image_desc = image_desc[2:]
    if image_desc.startswith('an '):
        image_desc = image_desc[3:]

    image_desc = image_desc.strip()

    # limit the length of the filename to 250 characters (to which the file extension will be added later
    # - adding '.jpeg' will make it 255 characters which is the maximum length for a file name on Windows & Mac)
    if len(image_desc) > 250:
        image_desc = image_desc[:250]

    return image_desc


def get_image_list(folder_path):
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg')) and len(f) <= MIN_CHARS_IN_FILENAME]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', default=None, type=str, help='Path to the folder to process')
    try:
        args = parser.parse_args()
        file_path = args.file_path
        if not file_path:
            file_path = input("\n\nPlease enter the path to the folder to process: ")
    except SystemExit:
        file_path = input("\n\nPlease enter the path to the folder to process: ")

    try:
        print('Ollama Image Describer describing files in folder:', file_path)

        image_list = get_image_list(file_path)
        print('Found a total of', len(image_list), 'images that require processing')

        well_described_counter = 0
        for image_full_file_path in image_list:
            print('Processing', image_full_file_path, '...')
            if is_image_well_described(image_full_file_path):
                print('    The image is well described - skipping...')
                well_described_counter += 1
            else:
                description = ''
                while (len(description) < 40 or
                       len(description) > 250 or
                       description.startswith('create') or
                       description.startswith('this') or
                       description.startswith('the')):
                    if description != '':
                        print('...the description suggested is not valid - having another go! Attempt was:"{}"'.format(description))
                    description = describe_image(image_full_file_path)

                # convert the description to be filename friendly and add the previous file extension
                new_file_name = convert_description_to_be_filename_friendly(description) + '.' + image_full_file_path.split('.')[-1]
                print('    New file name:', new_file_name)

                # rename the file to the new file name
                new_file_path = os.path.join(file_path, new_file_name)
                shutil.move(image_full_file_path, new_file_path)

        print('Ollama Image Describer finished processing', len(image_list), 'images, of which', well_described_counter,
              'were already well described, a percentage of', round(well_described_counter / len(image_list) * 100, 2), '%')
    except KeyboardInterrupt:
        print('Ollama Image Describer finished and can continue when you next restart it')
    except Exception as e:
        print('Error:', e)
        print('Ollama Image Describer finished with errors but will try to continue when you restart it')
