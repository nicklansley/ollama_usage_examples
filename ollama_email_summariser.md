# GMail Email Summarising Script

This script is designed to fetch and filter emails from a Gmail account within the past 24 hours, using IMAP. 
It then uses Ollama AI to summarise the content of the emails and then send a single summary email to the user.

## Prerequisites

- Python 3.9+
- Access to a Gmail account
- DotEnv and Ollama AI Python packages installed
- Ollama server running with an appropriate AI models loaded (see below)

## Requirements

Install the following Python packages using the `pip` installer:

```bash
pip install python_dotenv ollama
```

## Setup

### Gmail IMAP Configuration

1. **Enable IMAP in Gmail**:
    - Go to your Gmail account's settings.
    - Navigate to the "Forwarding and POP/IMAP" tab.
    - Enable IMAP.

2. **Allow Less Secure Apps**:
    - Go to your Google Account settings.
    - Navigate to the "Security" section.
    - Enable "Less secure app access". (Note: This setting may not be available if you have 2-Step Verification enabled. In that case, consider using an App Password).



## Running the Script

Set up a .env file with the following content:

```bash
GMAIL_USERNAME=you@your_gmail_hosted_email_address.com
GMAIL_PASSWORD=your_passwoerd
INDIVIDUAL_EMAIL_SUMMARIES=NO
```
You can set INDIVIDUAL_EMAIL_SUMMARIES to YES if you want to process each email with individual summaries.
This will take longer to run.

### Setting up the two models
The script uses two models - a large model for summarising and smaller (so faster) model for categorising.
Choose the two models that are as large as possible while still being able to run on your hardware in a reasonable time.
Make sure you have downloaded the models before running the script using the command:
```bash
ollama pull <model name>

```
Place the models towards the top of the script into these two variables:
```python
categorising_ai_model = 'llama3.1:latest'
summarising_ai_model = 'llama3.1:70b'
```
Finally, you probably don't want the script to summaruse your own messages. 
You can add your email address to the list of exclusions - and add other emails if you want to exclude them too.
```python
ignore_sender_list = ['you@your_gmail_hosted_email_address.com']
```

## Contributing

If you have suggestions or improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the terms of the MIT license.