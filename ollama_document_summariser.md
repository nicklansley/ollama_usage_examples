# Ollama Document Summariser

This script takes a Microsoft Word document as input, reads the content, and generates a summarized version of it using an AI model from Ollama AI. The user has the option to specify the desired word count for the summary (default is 1000 words).

## How It Works

The script can be broken down into several key steps:

1. **Reading the Word Document:** The script utilizes the python-docx library to open and read the content of the Word document, converting it to plain text.

2. **Sending Request to the AI Model:** The script sends a request to the Ollama AI model to summarize the extracted text document content. The maximum word count of the summary can be specified by the user.

3. **Receiving the Summary:** The AI model returns the summarized version of the document, which our script then captures.

4. **Writing the Summary:** The summarized content is then written to an output file specified by the user.

The script captures the total processing time and the evaluation time, which represents the time taken by the AI model to generate the summary.

## Usage

### File
Use --file to specify the path to the Word document you want to summarise.
### Wordcount
Use --wordcount to define the maximum number of words for the summary. If not provided, the default value is 1000.
### Output
Use --output to indicate the path to the file where the summarised text will be saved.
Please ensure your environment have Ollama AI SDK and python-docx library installed to run this script properly.
