from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from email.header import decode_header
import email
import email.message
import email.message
import imaplib
import json
import ollama
import os
import smtplib

load_dotenv()

# Assuming gmail_account_username and gmail_account_password are retrieved from environment variables
gmail_account_username = os.getenv('GMAIL_USERNAME')
gmail_account_password = os.getenv('GMAIL_PASSWORD')

# Create a separate .env file in the same directory as this script with the following content:
# GMAIL_USERNAME=<your gmail-hosted email address>
# GMAIL_PASSWORD=<your gmail app password>
# INDIVIDUAL_EMAIL_SUMMARIES=NO  (set to YES if you want individual email summaries)

messages_list = []

# List of sender email addresses to ignore when processing emails
ignore_sender_list = json.loads(os.getenv('IGNORE_SENDER_LIST', '[]'))

# Use a larger model for summarising email content *but not too large as it may take too long to summarise well*
summarising_ai_model = os.getenv("SUMMARISING_AI_MODEL", 'llama3.1:latest')
print('Using AI model for summarising email content:', summarising_ai_model)

INDIVIDUAL_EMAIL_SUMMARIES = os.getenv("INDIVIDUAL_EMAIL_SUMMARIES", "NO") == 'YES'
NEWSREADER_SCRIPT = os.getenv("NEWSREADER_SCRIPT", "NO") == 'YES'
HOURS_TO_FETCH = os.getenv("HOURS_TO_FETCH", 24)
if not HOURS_TO_FETCH.isdigit():
    HOURS_TO_FETCH = 24
else:
    HOURS_TO_FETCH = int(HOURS_TO_FETCH)

ai_model_content_prompt = """
You are a skilled scriptwriter for a news radio station. Summarise the email messages received over the past <HOURS_TO_FETCH> hours into a single paragraph for the next news bulletin.
The user will send you these emails and you must summarise them by repeating key details and highlighting anything notable.
Ensure the summary is engaging, informative, and concise, in one paragraph, without bullet points or lists, as it will be read aloud.
Do not start your summary with "Here is a summary" or similar words. Just dive straight in!
Use British English spelling. Optionally, you may add your opinion or observations starting with "In my opinion, " for the final sentence.
"""

ai_model_opening_summary_prompt = """
You are an expert report-writing author. You have been given a set of individual paragraphs. Each paragraph is a summary of an email received over the previous <HOURS_TO_FETCH> hours.
You are to author a conversation report which is a detailed 'summary of summaries' highlighting the major themes covered by these summaries so that the reader has a
clear and detailed idea of the range of subjects. You are welcome to offer your opinion on the importance or otherwise of these themes. What subjects resonate with you that you should highlight to the user? 
What subjects should the user concentrate on? What is important? What is not important? The user will reply on your expertise to guide them.
"""

ai_model_concluding_summary_prompt = """
You are an expert scriptwriter for a news radio station. You have been given the script for a news bulletin and you are to 
author a concluding paragraph using your own opinion and observations on these messages that have been received over the previous <HOURS_TO_FETCH> hours. 
Start the sentence with "In conclusion, "
"""


def format_body(body_text):
    # Array of search and replacement pairs
    replacements = [
        ('\n', ' '),
        ('\r', ' '),
        ('\t', ' '),
        ('\u200c', ' '),
        ('\u2019', ' '),
        ('\ud83d', ' '),
        ('\udc9a', ' '),
        ('\u00a9', ' '),
        ('\u2014', ' '),
        ('\u2013', ''),
        ('\u2012', ''),
        ('\u201c', ' '),
        ('\u201d', ''),
        ('\u2018', ' ')
    ]

    # Perform replacements using a loop
    for search, replacement in replacements:
        body_text = body_text.replace(search, replacement)

    while '  ' in body_text:
        body_text = body_text.replace('  ', ' ')

    word_list = body_text.split()
    formatted_word_list = []
    for word in word_list:
        if word.startswith('&') and word.endswith(';'):
            continue
        formatted_word_list.append(word)

    # join the words up together with spaces, excluding words over 15 characters (which are unlikely to be real words)
    return ' '.join([word for word in formatted_word_list if len(word) <= 15])


def get_gmail_messages():
    if not gmail_account_username or not gmail_account_password:
        print("Email gmail_account_username or gmail_account_password not set in environment variables or .env file")
        exit(1)

    mail = connect_to_server()

    message_id_list = get_all_message_ids(mail)

    print('Total emails found in Inbox:', len(message_id_list))

    messages_list = fetch_and_filter_messages(mail, message_id_list)

    print(len(messages_list), f'messages from the past {HOURS_TO_FETCH} hours to process')
    mail.logout()

    return messages_list


def connect_to_server():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(gmail_account_username, gmail_account_password)
    return mail


def get_all_message_ids(mail):
    try:
        # Select the INBOX
        status, messages = mail.select("inbox")
        if status != 'OK':
            print("Error selecting inbox!")
            return []

        # Calculate the IMAP date string for HOURS_TO_FETCH hours ago
        date_hours_ago = (datetime.now() - timedelta(hours=HOURS_TO_FETCH)).strftime('%d-%b-%Y')
        search_criteria = f'(SINCE {date_hours_ago})'

        status, data = mail.search(None, search_criteria)
        if status != 'OK':
            print("No messages found!")
            return []

        message_ids = data[0].split()
        return message_ids
    except Exception as e:
        print(f'Error fetching message IDs: {e}')
        return []


def fetch_and_filter_messages(mail, message_id_list):
    email_list = []
    counter = 0
    for current_email_id in message_id_list:
        msg = fetch_email_by_id(mail, current_email_id)
        msg_data = extract_email_data(msg)

        # Print a dot to indicate progress
        print('.', end='', flush=True)

        if msg_data['sender'] in ignore_sender_list:
            continue

        if msg_data['body'] and len(msg_data['body']) > 0:
            msg_data['summary'] = ''
            email_list.append(msg_data)
            counter += 1
            if counter % 50 == 0:
                print(f' - {counter}', end='', flush=True)
                print()

    print(
        f'{len(email_list)} messages found with readable text in the body of the message')  # Move to the next line after finishing
    return email_list


def fetch_email_by_id(mail, email_id):
    status, msg_data = mail.fetch(email_id, "(RFC822)")
    raw_email = msg_data[0][1]
    return email.message_from_bytes(raw_email)


def extract_email_data(msg):
    try:
        subject = decode_mime_header(msg["Subject"]).replace('\n', '')
    except:
        subject = '(no subject)'

    try:
        sender = msg.get("From")
    except:
        sender = '(unknown sender)'

    try:
        message_id = msg.get('Message-ID')
    except:
        message_id = '(unknown message id)'

    try:
        date_sent = msg.get("Date")
    except:
        date_sent = '(unknown date)'

    try:
        body = extract_body(msg)
    except:
        body = ''

    return {
        'message_id': message_id,
        'date_sent': date_sent,
        'sender': sender,
        'subject': subject,
        'body': format_body(body),
        'summary': ''
    }


def decode_mime_header(header_value):
    decoded_header, encoding = decode_header(header_value)[0]
    if isinstance(decoded_header, bytes):
        return decoded_header.decode(encoding or 'utf-8')
    return decoded_header


def extract_body(msg):
    body = ''

    def decode_payload(encoded_payload):
        # Decode only once and check for HTML
        if encoded_payload:
            decoded_payload = encoded_payload.decode(errors='ignore')
            if '<html' not in decoded_payload:
                return decoded_payload + "\n"
        return ''

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if "text/plain" in content_type:
                payload = part.get_payload(decode=True)
                body += decode_payload(payload)
    else:
        payload = msg.get_payload(decode=True)
        body += decode_payload(payload)

    return body


def ai_summarise_email(email_content):
    response = ollama.chat(
        model=summarising_ai_model,
        options={
            "num_ctx": 8000
        },
        messages=[
            {
                'role': 'system',
                'content': ai_model_content_prompt.replace('<HOURS_TO_FETCH>', str(HOURS_TO_FETCH)),

            },
            {
                'role': 'user',
                'content': email_content,
            },
        ])

    return response['message']['content'].strip().replace('\n', '.')


def call_ai_model(model, prompt, user_content, num_ctx=8000):
    response = ollama.chat(
        model=model,
        options={
            "num_ctx": num_ctx
        },
        messages=[
            {
                'role': 'system',
                'content': prompt,
            },
            {
                'role': 'user',
                'content': user_content,
            },
        ])

    return response['message']['content'].strip()


def update_message_list(message_id, summary):
    # update messages_list with summary by matching message_id
    for message in messages_list:
        if message['message_id'] == message_id:
            message['summary'] = summary
            break


def author_summary_email(email_list):
    # convert the messages_list data into an email message with the summaries
    earliest_message = email_list[0]["date_sent"]
    latest_message = email_list[len(email_list) - 1]["date_sent"]

    email_body = f"<p>Here are the AI-powered summaries of the emails from {earliest_message} to {latest_message} brought to you by {summarising_ai_model}:<br><br></p>"

    summaries = ''
    for message in email_list:
        summaries += f"{message['summary']}\n\n"

    print('Authoring top headlines summary...')
    updated_opening_summary_prompt = ai_model_opening_summary_prompt.replace('<HOURS_TO_FETCH>', str(HOURS_TO_FETCH))
    email_body += '<hr>Main Report:<br>' + call_ai_model(summarising_ai_model, updated_opening_summary_prompt,
                                                         summaries)

    print('Authoring concluding summary...')
    updated_conclusion_prompt = ai_model_concluding_summary_prompt.replace('<HOURS_TO_FETCH>', str(HOURS_TO_FETCH))
    email_body += '<hr>Concluding Paragraph:<br>' + call_ai_model(summarising_ai_model, updated_conclusion_prompt,
                                                                  summaries)

    return email_body, earliest_message, latest_message


def send_summary_email(email_body, earliest_datetime, latest_datetime):
    if not gmail_account_username or not gmail_account_password:
        print("Email gmail_account_username or gmail_account_password not set in environment variables or .env file")
        exit(1)

    # Connect to the server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        # Log in to the account
        server.login(gmail_account_username, gmail_account_password)

        # Create the email message
        msg = email.message.EmailMessage()
        msg['Subject'] = f'Summary of messages from {earliest_datetime} to {latest_datetime}'
        msg['From'] = gmail_account_username
        msg['To'] = gmail_account_username

        # Set the email content as HTML
        msg.add_alternative(email_body, subtype='html')

        # Send the email
        server.send_message(msg)


if __name__ == '__main__':
    try:
        start_time = datetime.now(timezone.utc)
        print(f'Starting email summarisation process at {start_time}')

        # check if file 'messages_list.json' exists and load it
        if os.path.exists('messages_list.json'):
            print('Loading messages_list from file')
            with open('messages_list.json', 'r') as f:
                messages_list = json.load(f)
        else:
            print('Fetching messages from Gmail')
            messages_list = get_gmail_messages()

        process_counter = 1

        for message in messages_list:
            if len(message['summary']) == 0:
                print('Processing message:', process_counter, 'of', len(messages_list))
                if len(message['body']) > 20:
                    message['summary'] = ai_summarise_email(message['body'])
                else:
                    message['summary'] = 'The email content was too short to summarise'
            else:
                print('Skipping message:', process_counter, 'of', len(messages_list), '- already summarised')

            # update messages with summary by matching message_id
            update_message_list(message['message_id'], message['summary'])

            # save message_list to a file in case of interruption
            with open('messages_list.json', 'w') as f:
                json.dump(messages_list, f, indent=4)

            process_counter += 1

        print('All emails summarised successfully - now authoring summary email')
        email_message, earliest_message_datetime, latest_message_datetime = author_summary_email(messages_list)

        print('Now sending summary email to', gmail_account_username)
        send_summary_email(email_message, earliest_message_datetime, latest_message_datetime)

        # Success! Now delete the messages_list file
        os.remove('messages_list.json')

        end_time = datetime.now(timezone.utc)
        print(f'Email summarisation process completed at {end_time}')
        print(f'Total time taken: {end_time - start_time}')

    except KeyboardInterrupt:
        print('Process interrupted by user')
        exit(0)

    except Exception as e:
        print('Error:', e)
        exit(1)
