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
messages_list = []

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
You are an expert at categorising email messages.
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
Only provide your chosen single one category word, and no other words or phrases.
If you don't do this, the email will be rejected.
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

    # Connect to the server
    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    # Log in to the account
    mail.login(gmail_account_username, gmail_account_password)

    # Select the mailbox (in this case, the inbox)
    typ, data = mail.select(mailbox="INBOX")

    # Search for all emails in the inbox
    status, messages = mail.search(None, "ALL")

    # Convert messages to a list of email IDs
    message_id_list = messages[0].split()
    print('Total emails:', len(message_id_list))

    # The latest email is the last one in the list, and we need to reverse the list to get the latest email first
    message_id_list.reverse()

    # Remove the email IDs that are after the first 100 emails
    if len(message_id_list) > MAX_MESSAGES_TO_PROCESS:
        message_id_list = message_id_list[:MAX_MESSAGES_TO_PROCESS]

    # Get the latest 100 emails
    for current_email_id in message_id_list:
        # Fetch the email by ID
        status, msg_data = mail.fetch(current_email_id, "(RFC822)")

        # Get the email content
        raw_email = msg_data[0][1]

        # Parse the email content
        msg = email.message_from_bytes(raw_email)

        # Decode unique message id
        message_id = msg.get('Message-ID')
        print(f"\nMessage ID: {message_id}")

        # Decode email sender and subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            if encoding:
                subject = subject.decode(encoding)
            else:
                subject = subject.decode()
        sender = msg.get("From")

        date_sent = msg.get("Date")
        print(f"Date: {date_sent}")
        print(f"From: {sender}")
        print(f"Subject: {subject}")

        # Extract the email body
        body = ''

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if "text/plain" in content_type:
                    payload = part.get_payload(decode=True)
                    if payload:
                        decoded_payload = payload.decode(errors='ignore')
                        if '<html' not in decoded_payload:
                            body += decoded_payload + "\n"
                        # print("Body:", body)

            message_data = {
                'message_id': message_id,
                'date_sent': date_sent,
                'sender': sender,
                'subject': subject,
                'body': format_body(body),
                'summary': ''
            }
            if message_data['body'] != '':
                messages_list.append(message_data)

            # save messages_List so far to a file
            with open('messages_list_1.json', 'w') as f:
                json.dump(messages_list, f)

        else:
            payload = msg.get_payload(decode=True)
            decoded_payload = payload.decode(errors='ignore')

            if '<html' not in decoded_payload:
                body += decoded_payload + "\n"

            message_data = {
                'message_id': message_id,
                'date_sent': date_sent,
                'sender': sender,
                'subject': subject,
                'body': format_body(body),
                'summary': ''
            }

            if message_data['body'] != '':
                messages_list.append(message_data)

            # save messages_List so far to a file
            with open('messages_list_1.json', 'w') as f:
                json.dump(messages_list, f)
            # print("Body:", body)

    # Logout and close the connection
    mail.logout()

    return messages_list


def describe_email(email_message):
    response = ollama.chat(
        model='phi3:medium',
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
    response = ollama.chat(
        model='phi3:medium',
        messages=[
            {
                'role': 'system',
                'content': ai_model_category_prompt,

            },
            {
                'role': 'user',
                'content': f"Hello! Please give me your recommended cateogory for this email message: '{email_message}'",
            },
        ])

    return response['message']['content'].strip().replace('\n', '.')


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
    for message in messages_list:
        email_message += f"From: {message['sender']}\n"
        try:
            email_message += f"Date: {message['date_sent']}\n"
        except:
            email_message += "Date: (unknown)\n"
        email_message += f"Subject: {message['subject']}\n"
        email_message += f"Category: {message['category']}\n"
        email_message += f"Summary: {message['summary']}\n\n"
        email_message += '----------------------------------------\n\n'
    return email_message, earliest_message, latest_message


def send_summary_email(email_message, earliest_message_datetime, latest_message_datetime):
    # Account credentials
    gmail_account_username = os.getenv("GMAIL_USERNAME")
    gmail_account_password = os.getenv("GMAIL_PASSWORD")

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
