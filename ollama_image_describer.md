# Ollama Image Describer

This Python script uses the Ollama API to generate
a description of an image.

The main functionality is defined in the function
`describe_image(image_file_path)`.

The script also includes a snippet
for command - line argument parsing, so it can be used straight from the terminal.

## Import Statements

The script begins with importing the necessary modules and packages.
It imports 'ollama' for generating image descriptions, 'os' and '
shutil' to handle file and directory operations, and 'argparse' for command-line argument parsing.

## Description Prompt
A predefined prompt is set as a multi-line string to guide the Ollama model in generating descriptions.

## Function - describe_image()
The function describe_image(image_file_path) takes an image file path as an argument, opens the image for reading in binary mode, uses the Ollama API to chat with the 'llava:34b' model, and returns the model's response.

## Main Execution
The script uses argparse to handle command-line arguments, expecting a file path to the image. It then calls the describe_image() function using the provided file path, prints the returned description, and handles any potential exceptions.


