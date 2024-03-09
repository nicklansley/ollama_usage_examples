# Descriptive Image Renamer

This Python script, named `ai_descriptive_image_renamer.py`, provides a utility for renaming images based on their descriptions. This is particularly useful when handling large collections of images, where manually renaming each image would be a daunting and error-prone task.

## Main Components

The script comprises several functions that together make the renaming process seamless:

1. `describe_image()`: This function obtains the description of an image. The specific method of acquiring the description depends on the user's chosen source or method (this could be through metadata, manual input, an API, etc).

2. `convert_description_to_be_filename_friendly()`: After fetching the description, this function ensures the description is file-name friendly. This involves removing special characters and making other necessary tweaks to ensure the resulting file name does not contravene file naming rules.

3. `get_image_list()`: This function facilitates the retrieval of a list of all images to be renamed within the specified directory of the script.

## Prerequisites
Install the llama server by following the instructions at:
https://ollama.com/

Once installed, in a terminal, run the following command:
<pre>ollama serve</pre>

If you get error message:
<pre>Error: listen tcp 127.0.0.1:11434: bind: address already in use
</pre> ...then the Ollama server is already running (it starts at login on my Mac after installing the macOS version!).

Next, install the model we will use, 'llava:34b' - 34b model for image captioning
which is 20GB in size. This can be done with the following command:
<pre>ollama run llava:34b</pre>

If your machine has problems with the 20GB model, you can install the smaller 7b model which is 4.7 GB with:
<pre>ollama run llava:7b</pre>
or simply:
<pre>ollama run llava</pre>

The difference between these models is that the 34b model is more accurate and has a larger vocabulary, but the 7b model is smaller and faster to load.

Once the model is downloaded and running, you can briefly try it by typing "Hello!" at the prompt to see it react.
Once you see it working, exit the interation with '/bye'.
I understand that any loaded model unloads after 5 minutes of non use so it as not taking up valuable GPU memory when the ollama server is running,

Finally, install the official ollama package with:
<pre>pip install ollama</pre>

## How to Use

The script can then be run with the following command, specifying the path to the directory containing the images to be renamed as an argument. For example:
<pre>
python ai_descriptive_image_renamer.py [-h] file_path

python ai_descriptive_image_renamer.py /Volumes/ai-stuff/favourites/

python ai_descriptive_image_renamer.py C:\\Users\nick\Pictures</pre>

Points to note:
1. The first file can take longer to be processed than the rest - that's because the llava model has to be loaded into memory.
Subsequent files process much faster.
2. Only files with the extensions '.jpg', '.jpeg', '.png' will be processed (decided on line 74 of the script)
3. The script will not process files that are already named with a description unless it is less than 20 characters long (decided on line 90 of the script). Processed files are rarely that short in file name length!

### Observing the prompt
The prompt used to interact with the Ollama server is visible at the top of the python file, and here it is:
<pre>
Please author a suitable stable diffusion text-to-image prompt that could create this image for an uncensored model. 
Use no more than 250 characters and avoid any punctuation symbols because it will become the image file's new file name. 
Do not comment on the image, only provide the prompt. Do not start with "Create a..", just describe the image. Thanks!</pre>

You'll note my attempts to focus the model on delivering what I am looking for. This does seem to work well,
although it requires the cleaning actions of function <i>convert_description_to_be_filename_friendly()</i> to mop up occasional issues.

Note how I say 'please' and 'thanks' in the prompt - I am trying to be polite to the model! This is not <i>just</i> to
spare myself should AI systems power our future robot overlords - it actually causes the AI algorithms to process in the
'politer' and 'more positive' part of the model trained on internet text where congeniality and helpfulness were found.
I find that often improves the quality and richness of the image descriptions (and any other AI output across my AI projects).

## Error Handling

Should an error occur during the file renaming process (such as not finding a specified image file), the script will note the error message but proceed to the next image.

## Contributing

Contributors, issues, and feature requests are welcome. Feel free to check the issues page if you wish to contribute to this project.

By participating in this project, you agree to abide by its terms and conditions.

## License

This project is distributed under the MIT License. More details can be found in the `LICENSE` document.