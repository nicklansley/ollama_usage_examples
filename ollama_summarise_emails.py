import json
import ollama
import email
from email.header import decode_header
import imaplib
from dotenv import load_dotenv
import os
import email.message
import smtplib

load_dotenv()
# Create a separate .env file in the same directory as this script with the following content:
# GMAIL_USERNAME=<your gmail-hosted email address>
# GMAIL_PASSWORD=<your gmail app password>
# GET_LATEST_MESSAGES=YES
# USE_AI_TO_SUMMARISE=YES
messages_list = []

ignore_sender_list = ['nick@lansley.com']
ai_model = 'llama3.1:latest'

# Account credentials
gmail_account_username = os.getenv("GMAIL_USERNAME")
gmail_account_password = os.getenv("GMAIL_PASSWORD")

ai_model_content_prompt = """
You are an expert at summarising email messages. 
You prefer to use clauses instead of complete sentences in order to make your summary concise and to the point.
Please be brief and to the point in a single paragraph. Don't use bullet points, lists, or other structured formats.
Do not answer any questions you may find in the messages. 
The user will provide you with a message to summarise.
"""

ai_model_category_prompt = """
You are an expert at categorising email messages into different categories.
When given an email message, you can categorise it using a single category from the following list
or you can choose a category of your own as long as it is a single word:
- Work
- Personal
- Social
- Promotional
- News
- Sport
- Health
- Finance
- Education
- Travel
- Food
- Technology
- Entertainment
- Shopping
- Legal
- Charity
- Government
- Religion
- Science
- Environment
- LGBTQ+

Please provide the category of the email message you think most closely matches the content.
Respond only with a single word. If you don't do this, the email will be rejected.
"""


ai_model_overall_summary_prompt = """
You are an expert at summarising email messages.
The user will send you a list of email messages and ask you to summarise them into a single paragraph.
Please summarise the emails into a single paragraph, highlighting anything notable.
Don't say you are summarising the emails, just do it!
"""


MAX_MESSAGES_TO_PROCESS = 10


def format_body(body_text):
    # remove newlines, carriage returns, weird characters and extra spaces
    body_text = body_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').replace('\u200c', ' ')
    body_text = body_text.replace('\u2019', ' ').replace('\ud83d', ' ').replace('\udc9a', ' ').replace('\u00a9', ' ')
    body_text = body_text.replace('\u2014', ' ').replace('\u2013', '').replace('\u2012', '').replace('\u201c', ' ')
    body_text = body_text.replace('\u201d', '').replace('\u2018', ' ')

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

    print('Total emails:', len(message_id_list))

    messages_list = process_messages(mail, message_id_list)

    mail.logout()

    return messages_list


def connect_to_server():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(gmail_account_username, gmail_account_password)
    return mail


def get_all_message_ids(mail):
    mail.select(mailbox="INBOX")
    status, messages = mail.search(None, "ALL")
    message_id_list = messages[0].split()
    message_id_list.reverse()
    return message_id_list


def process_messages(mail, message_id_list):
    messages_list = []
    for current_email_id in message_id_list:
        if len(messages_list) > MAX_MESSAGES_TO_PROCESS:
            break

        msg = fetch_email_by_id(mail, current_email_id)
        msg_data = extract_email_data(msg)

        if msg_data['sender'] in ignore_sender_list:
            continue

        if msg_data['body'] and len(msg_data['body']) > 0:
            messages_list.append(msg_data)
            save_messages_list_to_file(messages_list)

    return messages_list


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
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if "text/plain" in content_type:
                payload = part.get_payload(decode=True)
                if payload and '<html' not in payload.decode(errors='ignore'):
                    body += payload.decode(errors='ignore') + "\n"
    else:
        payload = msg.get_payload(decode=True)
        if '<html' not in payload.decode(errors='ignore'):
            body += payload.decode(errors='ignore') + "\n"
    return body


def save_messages_list_to_file(messages_list):
    with open('messages_list_1.json', 'w') as f:
        json.dump(messages_list, f)


def describe_email(email_message):
    response = ollama.chat(
        model=ai_model,
        messages=[
            {
                'role': 'system',
                'content': ai_model_content_prompt,

            },
            {
                'role': 'user',
                'content': f"Hello! Please use your expertise to summarise this email: '{email_message}'",
            },
        ])

    return response['message']['content'].strip().replace('\n', '.')


def categorise_email(email_message):
    chosen_category = ' '

    # The AI should respond with a single word (no spaces). If it does not, make it try again until it does!
    # This is to ensure that the AI does not provide a multi-word category
    attempt_count = 0
    while ' ' in chosen_category and attempt_count < 5:
        if len(chosen_category) > 1:
            print('AI did not provide a single word category. Trying again...')
            print('AI response:', chosen_category)
        response = ollama.chat(
            model=ai_model,
            messages=[
                {
                    'role': 'system',
                    'content': ai_model_category_prompt,

                },
                {
                    'role': 'user',
                    'content': f"Hello! Please give me your recommended category for this email message: '{email_message}'",
                },
            ])

        chosen_category = response['message']['content'].strip().replace('\n', '.')
        attempt_count += 1

    if ' ' in chosen_category and len(chosen_category) > 1:
        chosen_category = 'Other'
        print('AI did not provide a single word category. Using default category:', chosen_category)
    else:
        print('AI good category response:', chosen_category)

    return chosen_category


def summarise_email_list(email_message_list):
    content = 'Hello, please can you summarise the following emails into a single paragraph, highlighting anything notable:\n\n'
    for message in email_message_list:
        content += f"From: {message['sender']}\n"
        content += f"Subject: {message['subject']}\n"
        content += f"Body: {message['body']}\n\n"

    response = ollama.chat(
        model=ai_model,
        messages=[
            {
                'role': 'system',
                'content': ai_model_overall_summary_prompt,
            },
            {
                'role': 'user',
                'content': content,
            },
        ])

    ai_response = response['message']['content'].strip().replace('\n', '.')

    # Despite being told not to (!) the AI sometimes starts the summary with a sentence that is a variant of:
    # "Here is a summary of the emails in a single paragraph".
    # We remove this sentence if any of the following keywords are present: 'summary', 'paragraph', 'email'.
    # We deo this by breaking the string into a list of sentences and removing the first one, then
    # joining the sentences back together again.
    ai_response_sentences = ai_response.split('.')
    if 'summary' in ai_response_sentences[0] or 'paragraph' in ai_response_sentences[0] or 'email' in ai_response_sentences[0]:
        ai_response_sentences.pop(0)

    # Check for any empty-sentence strings and remove them
    ai_response_sentences = [sentence for sentence in ai_response_sentences if sentence]

    ai_response = '.'.join(ai_response_sentences)

    return ai_response


def update_message_list(message_id, summary):
    # update messages_list with summary by matching message_id
    for message in messages_list:
        if message['message_id'] == message_id:
            message['summary'] = summary
            print('Updating message with summary:', summary)
            break


def author_summary_email(messages_list):
    # convert the messages_list data into an email message with the summaries
    latest_message = messages_list[0]["date_sent"]
    earliest_message = messages_list[len(messages_list) - 1]["date_sent"]

    email_message = f'Here are the summaries of the emails from {earliest_message} to {latest_message}:\n\n'

    # create a list of categories found in messages_list
    categories_list = []
    for message in messages_list:
        if message['category'] not in categories_list:
            categories_list.append(message['category'])


    for category in categories_list:
        filtered_messages_list = [message for message in messages_list if message['category'] == category]
        email_message += f'Category: {category}\n\n'
        email_message += 'In ' + category + ', ' + summarise_email_list(filtered_messages_list)
        email_message += '\n\n'

    for message in messages_list:
        email_message += '----------------------------------------\n\n'
        email_message += f"From: {message['sender']}\n"
        try:
            email_message += f"Date: {message['date_sent']}\n"
        except:
            email_message += "Date: (unknown)\n"
        email_message += f"Subject: {message['subject']}\n"
        email_message += f"Category: {message['category']}\n"
        email_message += f"Summary: {message['summary']}\n\n"
    return email_message, earliest_message, latest_message


def send_summary_email(email_message, earliest_message_datetime, latest_message_datetime):
    if not gmail_account_username or not gmail_account_password:
        print("Email gmail_account_username or gmail_account_password not set in environment variables or .env file")
        exit(1)

    # Connect to the server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        # Log in to the account
        server.login(gmail_account_username, gmail_account_password)

        # Create the email message
        msg = email.message.EmailMessage()
        msg.set_content(email_message)
        msg['Subject'] = f'Summary of messages from {earliest_message_datetime} to {latest_message_datetime}'
        msg['From'] = gmail_account_username
        msg['To'] = gmail_account_username

        # Send the email
        server.send_message(msg)


if __name__ == '__main__':
    try:
        if os.getenv('GET_LATEST_MESSAGES') == 'YES':
            messages_list = get_gmail_messages()

        else:
            with open('messages_list_1.json', 'r') as f:
                messages_list = json.load(f)

        if os.getenv('USE_AI_TO_SUMMARISE') == 'YES':
            for message in messages_list:
                email_text = message['body']
                message['summary'] = describe_email(email_text)
                message['category'] = categorise_email(email_text)

                print('Message from:', message['sender'], 'with subject:', message['subject'])
                print('AI Summary:', message['summary'])
                print('AI Category:', message['category'])
                print()

                # update messages with summary by matching message_id
                update_message_list(message['message_id'], message['summary'])

                # save messages_List so far to a file
                with open('messages_list_1.json', 'w') as f:
                    json.dump(messages_list, f)
        else:
            with open('messages_list_1.json', 'r') as f:
                messages_list = json.load(f)

        print('All emails summarised successfully - now authoring and sending summary email to', gmail_account_username)
        email_message, earliest_message_datetime, latest_message_datetime = author_summary_email(messages_list)
        send_summary_email(email_message, earliest_message_datetime, latest_message_datetime)


    except KeyboardInterrupt:
        with open('messages_list_1.json', 'w') as f:
            json.dump(messages_list, f)
        print('Process interrupted by user')
        exit(0)

    except Exception as e:
        with open('messages_list_1.json', 'w') as f:
            json.dump(messages_list, f)
        print('Error:', e)
        exit(1)