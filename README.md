# Ollama Usage Examples
### Ollama AI Python Script-based Projects

For each script see its .md equivalent for more detailed information.

* [Descriptive Image Renamer](ai_descriptive_image_renamer.md) (Loops through a folder of images and renames them to reflect their content)
* [Document Summariser](ollama_document_summariser.md) (summarises text in Microsoft Word documents)
* [Email Summariser](ollama_email_summariser.md) (summarises text in emails)
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

The 'ollama_two_AIs_chat.py' script does NOT use the Ollama package so that package doesn't need to be installed, but if you use the scripts it does need to be installed. 
This can be done with:
<pre>pip install ollama</pre>