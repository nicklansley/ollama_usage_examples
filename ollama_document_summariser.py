import ollama
import argparse
from docx import Document


# this function reads a Microsoft Word document and returns the content
# as a plain text string. It uses the python-docx library to read the document
def read_word_document(document_file_path):
    text = ''
    with open(document_file_path, 'rb') as file:
        document = Document(file)
        for paragraph in document.paragraphs:
            text += paragraph.text + '\n'
    return text


def summarise_text(text, word_count):
    print('Sending text to the AI model for summarisation...')
    ai_model_content_prompt = "Please summarize this document using no more than {} words. Here is the document:".format(word_count)
    response = ollama.chat(
        model='command-r:35b',
        messages=[
            {
                'role': 'user',
                'content': ai_model_content_prompt + text
            },
        ],
    )

    if response['message']['content']:
        return response['message']['content'], int(response['total_duration'] / 1000000000), int(response['eval_duration'] / 1000000000)

    return 'Nothing was returned from the AI model. Please try again.', 0, 0


def word_wrap_text(text, max_length):
    words = text.split(' ')
    lines = []
    line = ''
    for word in words:
        if len(line) + len(word) + 1 <= max_length:
            line += word + ' '
        else:
            lines.append(line)
            line = word + ' '

    if line:
        lines.append(line)

    return '\n'.join(lines)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, help='Path to the document to read and summarise')
    parser.add_argument('--wordcount', type=str, help='Count of words to be used in the summary', default=1000)
    parser.add_argument('--wordwrap', type=str, help='Optional word-wrap after n characters', default=None)
    parser.add_argument('--output', type=str, help='Path to save the summarised text to')
    args = parser.parse_args()

    try:
        print('Ollama Document Summariser reading document:', args.file)
        output_word_count = int(args.wordcount)
        word_text = read_word_document(args.file)
        print('The number of words to send to the LLM model:', len(word_text.split(' ')))
        output, total_duration, eval_duration = summarise_text(word_text, output_word_count)

        if args.wordwrap:
            output = word_wrap_text(output, int(args.wordwrap))

        with open(args.output, 'w') as file:
            file.write(output)

        print('Completed - results saved to "{}" using {} words.'.format(args.output, len(output.split(' '))))

        if args.wordwrap:
            print('The output has been word-wrapped after every {} characters.'.format(args.wordwrap))
        print('Total processing time was {} seconds of which evaluation took {} seconds.'.format(total_duration, eval_duration))

    except Exception as e:
        print('Error:', e)
