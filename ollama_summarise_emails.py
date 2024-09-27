import email
import email.message
import imaplib
import os
from datetime import datetime, timedelta, timezone
from email.header import decode_header
import smtplib
from dotenv import load_dotenv
import ollama

load_dotenv()

class EmailSummarizer:
    def __init__(self):
        self.gmail_account_username = os.getenv("GMAIL_USERNAME")
        self.gmail_account_password = os.getenv("GMAIL_PASSWORD")
        self.INDIVIDUAL_EMAIL_SUMMARIES = os.getenv("INDIVIDUAL_EMAIL_SUMMARIES", "NO") == "YES"
        self.NEWSREADER_SCRIPT = os.getenv("NEWSREADER_SCRIPT", "NO") == "YES"

        self.HOURS_TO_FETCH = os.getenv("HOURS_TO_FETCH", "24")
        self.HOURS_TO_FETCH = int(self.HOURS_TO_FETCH) if self.HOURS_TO_FETCH.isdigit() else 24

        self.ignore_sender_list = ["nick@lansley.com"]
        self.messages_list = []

        self.categorising_ai_model = os.getenv("CATEGORISING_AI_MODEL", 'llama3.1:latest')
        self.summarising_ai_model = os.getenv("SUMMARISING_AI_MODEL", 'llama3.1:latest')

        self.init_ai_prompts()

    def init_ai_prompts(self):
        self.ai_model_content_prompt = """
        You are an expert at summarising email messages. 
        You prefer to use clauses instead of complete sentences in order to make your summary concise and to the point.
        Be brief and to the point in a single paragraph. Don't use bullet points, lists, or other structured formats.
        Do not answer any questions you may find in the messages. Use British English spelling.
        The user will provide you with a message to summarise. This message will have been received within the previous <HOURS_TO_FETCH> hours.
        """.replace('<HOURS_TO_FETCH>', str(self.HOURS_TO_FETCH))

        self.ai_model_category_prompt = """
        You are an expert at categorising email messages using a single word category name.
        If necessary you can choose a category of your own as long as it is a single word.
        Please provide the category of the email message you think most closely matches the content.
        You must respond with only a single word which is your chosen category. Do not respond with multiple words or sentences.
        Here is a list of possible categories:
        - Business, Charity, Education, Entertainment, Environment, Finance, Food, Government, Health, LGBTQ+, Legal,
          News, Personal, Promotional, Religion, Science, Shopping, Social, Sport, Technology, Travel, Work
        """.replace('<HOURS_TO_FETCH>', str(self.HOURS_TO_FETCH))

        self.ai_model_top_headlines_prompt = """
        You are an expert scriptwriter for a news radio station. You are tasked with creating headlines based on the emails that 
        have arrived over the past <HOURS_TO_FETCH> hours into a single paragraph that will be read aloud at the next news bulletin. 
        The user will send you a list of email messages received over the previous <HOURS_TO_FETCH> hours and ask you to 
        summarise them as headlines, highlighting anything notable. Your summary needs to be engaging and informative, holding the listener's attention as the news bulletin starts.
        Please be brief and to the point in a single paragraph. Use British English spelling.
        For the final sentence you may add your own opinion or observations on these messages. If you do, start the sentence with "In my opinion, "
        """.replace('<HOURS_TO_FETCH>', str(self.HOURS_TO_FETCH))


        self.ai_model_category_headlines_prompt = """
        You are an expert scriptwriter for a news radio station. You are tasked with summarising a list of email messages that 
        have arrived over the past <HOURS_TO_FETCH> hours into a single paragraph that will be read aloud at the next news bulletin. 
        The user will send you a list of email messages received over the previous <HOURS_TO_FETCH> hours and ask you to 
        summarise them, highlighting anything notable. Your summary needs to be engaging and informative, even if the emails are not.
        Please be brief and to the point in a single paragraph. Use British English spelling.
        For the final sentence you may add your own opinion or observations on these messages. If you do, start the sentence with "In my opinion, "
        """.replace('<HOURS_TO_FETCH>', str(self.HOURS_TO_FETCH))

        self.ai_model_concluding_summary_prompt = """
        You are an expert scriptwriter for a news radio station. You have been given the script for a news bulletin and you are to 
        author a concluding paragraph using your own opinion and observations on these messages that have been received over the previous <HOURS_TO_FETCH> hours. 
        Start the sentence with "In conclusion, "
        """.replace('<HOURS_TO_FETCH>', str(self.HOURS_TO_FETCH))


    @staticmethod
    def format_body(body_text: str) -> str:
        replacements = [
            ('\n', ' '), ('\r', ' '), ('\t', ' '), ('\u200c', ' '), ('\u2019', ' '), ('\ud83d', ' '), ('\udc9a', ' '),
            ('\u00a9', ' '), ('\u2014', ' '), ('\u2013', ''), ('\u2012', ''), ('\u201c', ' '), ('\u201d', ''), ('\u2018', ' ')
        ]

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
        return ' '.join([word for word in formatted_word_list if len(word) <= 15])

    def get_gmail_messages(self):
        if not self.gmail_account_username or not self.gmail_account_password:
            print("Email gmail_account_username or gmail_account_password not set in environment variables or .env file")
            exit(1)

        mail = self.connect_to_server()
        message_id_list = self.get_all_message_ids(mail)
        print('Total emails found in Inbox:', len(message_id_list))
        messages_list = self.fetch_and_filter_messages(mail, message_id_list)
        print(len(messages_list), f'messages from the past {self.HOURS_TO_FETCH} hours to process')
        mail.logout()
        return messages_list

    def connect_to_server(self):
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(self.gmail_account_username, self.gmail_account_password)
        return mail

    def get_all_message_ids(self, mail):
        try:
            status, messages = mail.select("inbox")
            if status != 'OK':
                print("Error selecting inbox!")
                return []

            date_hours_ago = (datetime.now() - timedelta(hours=self.HOURS_TO_FETCH)).strftime('%d-%b-%Y')
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

    def fetch_and_filter_messages(self, mail, message_id_list):
        email_list = []
        counter = 0
        for current_email_id in message_id_list:
            msg = self.fetch_email_by_id(mail, current_email_id)
            msg_data = self.extract_email_data(msg)
            print('.', end='', flush=True)

            if msg_data['sender'] in self.ignore_sender_list:
                continue

            if msg_data['body'] and len(msg_data['body']) > 0:
                email_list.append(msg_data)
                counter += 1
                if counter % 50 == 0:
                    print(f' - {counter}', end='', flush=True)
                    print()

        print(f'{len(email_list)} messages found with readable text in the body of the message')
        return email_list

    def fetch_email_by_id(self, mail, email_id):
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        return email.message_from_bytes(raw_email)

    def extract_email_data(self, msg) -> dict:
        try:
            subject = self.decode_mime_header(msg["Subject"]).replace('\n', '')
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
            body = self.extract_body(msg)
        except:
            body = ''

        return {
            'message_id': message_id, 'date_sent': date_sent, 'sender': sender, 'subject': subject, 'body': self.format_body(body), 'summary': ''
        }

    @staticmethod
    def decode_mime_header(header_value: str) -> str:
        decoded_header, encoding = decode_header(header_value)[0]
        if isinstance(decoded_header, bytes):
            return decoded_header.decode(encoding or 'utf-8')
        return decoded_header

    @staticmethod
    def extract_body(msg):
        body = ''

        def decode_payload(encoded_payload):
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

    def ai_summarise_email(self, email_content: str) -> str:
        response = ollama.chat(
            model=self.summarising_ai_model,
            options={"num_ctx": 8000},
            messages=[
                {'role': 'system', 'content': self.ai_model_content_prompt},
                {'role': 'user', 'content': email_content},
            ])
        return response['message']['content'].strip().replace('\n', '.')

    def call_ai_model(self, model, prompt, user_content, num_ctx=8000):
        response = ollama.chat(
            model=model, options={"num_ctx": num_ctx},
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': user_content},
            ])

        return response['message']['content'].strip()


    def ai_categorise_email(self, email_content: str) -> str:
        chosen_category = ' '
        attempt_count = 0

        while ' ' in chosen_category and attempt_count < 5:
            chosen_category = self.call_ai_model(
                self.categorising_ai_model, self.ai_model_category_prompt, email_content
            ).replace('\n', '.').strip()
            attempt_count += 1

        if ' ' in chosen_category and len(chosen_category) > 1:
            chosen_category = 'Other'

        return chosen_category.upper()


    def ai_author_category_headlines(self, email_message_list: list) -> str:
        content = ''.join(
            f"From: {message_data['sender']}\nSubject: {message_data['subject']}\nBody: {message_data['body']}\n\n"
            for message_data in email_message_list)

        ai_response = self.call_ai_model(
            self.summarising_ai_model, self.ai_model_category_headlines_prompt, content
        ).replace('\n', '. ')

        ai_response_sentences = [sentence for sentence in ai_response.split('. ') if 'summary' not in sentence and 'paragraph' not in sentence and sentence]
        ai_response = '. '.join(ai_response_sentences)

        if 'In my opinion' in ai_response:
            ai_response = '<p>' + ai_response.replace('In my opinion', '<br><br><i>In my opinion') + '</i></p>'
        else:
            ai_response = '<p>' + ai_response + '</p>'

        if ai_response.startswith('"') and ai_response.endswith('"'):
            ai_response = ai_response[1:-1]

        return ai_response + '. '

    def ai_author_concluding_paragraph(self, email_body_text: str) -> str:
        print('Authoring concluding paragraph...')
        return self.call_ai_model(
            self.summarising_ai_model, self.ai_model_concluding_summary_prompt, email_body_text
        )

    def ai_author_overall_headlines(self, summarised_group_content: str) -> str:
        print('Authoring top headlines summary...')
        return self.call_ai_model(
            self.summarising_ai_model, self.ai_model_top_headlines_prompt, summarised_group_content
        )

    def update_message_list(self, message_id: str, summary: str):
        for message in self.messages_list:
            if message['message_id'] == message_id:
                message['summary'] = summary
                break

    def author_summary_email(self, email_list: list) -> tuple:
        earliest_message = email_list[0]["date_sent"]
        latest_message = email_list[-1]["date_sent"]

        email_body = f"<p>Here are the AI-powered summaries of the emails from {earliest_message} to {latest_message}:<br><br></p>"
        categories_list = sorted(set(message["category"] for message in email_list))

        if 'PERSONAL & SOCIAL' in categories_list:
            categories_list.remove('PERSONAL & SOCIAL')
            categories_list.insert(0, 'PERSONAL & SOCIAL')

        if 'NEWS' in categories_list:
            categories_list.remove('NEWS')
            categories_list.insert(1, 'NEWS')

        category_counter = 0
        for category in categories_list:
            category_counter += 1
            filtered_messages_list = [message for message in email_list if message["category"] == category]
            print(f'Processing category: {category} ({category_counter} of {len(categories_list)}) - {len(filtered_messages_list)} messages...')
            email_body += f'<hr>Category: {category} (from {len(filtered_messages_list)} messages)<br>'
            for i in range(0, len(filtered_messages_list), 10):
                email_body += f' >>> {category}-{i+1}-{i+10}<br>'
                email_body += self.ai_author_category_headlines(filtered_messages_list[i:i + 10])
                email_body += '\n\n'

        if self.NEWSREADER_SCRIPT:
            email_body = '<p>Overall Headline Summary:<br>' + self.ai_author_overall_headlines(email_body) + '<br><br>' + email_body + '</p>'

        if self.INDIVIDUAL_EMAIL_SUMMARIES:
            for message in email_list:
                email_body += '----------------------------------------<br><br>'
                email_body += f"From: {message['sender']}<br>"
                email_body += f"Date: {message.get('date_sent', 'unknown')}<br>"
                email_body += f"Subject: {message['subject']}<br>"
                email_body += f"Category: {message['category']}<br>"
                email_body += f"Summary: {message['summary']}<br><br>"

        email_body += '<hr>Concluding Paragraph:<br>' + self.ai_author_concluding_paragraph(email_body)
        return email_body, earliest_message, latest_message

    def send_summary_email(self, email_body: str, earliest_datetime: str, latest_datetime: str):
        if not self.gmail_account_username or not self.gmail_account_password:
            print("Email gmail_account_username or gmail_account_password not set in environment variables or .env file")
            exit(1)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.gmail_account_username, self.gmail_account_password)
            msg = email.message.EmailMessage()
            msg['Subject'] = f'Summary of messages from {earliest_datetime} to {latest_datetime}'
            msg['From'] = self.gmail_account_username
            msg['To'] = self.gmail_account_username
            msg.add_alternative(email_body, subtype='html')
            server.send_message(msg)

    def run(self):
        try:
            start_time = datetime.now(timezone.utc)
            print(f'Starting email summarisation process at {start_time}')

            self.messages_list = self.get_gmail_messages()
            process_counter = 1

            for message in self.messages_list:
                print('Processing message:', process_counter, 'of', len(self.messages_list))
                email_text = message['body']
                message['category'] = self.ai_categorise_email(email_text)

                if self.INDIVIDUAL_EMAIL_SUMMARIES:
                    message['summary'] = self.ai_summarise_email(email_text)

                self.update_message_list(message['message_id'], message['summary'])
                process_counter += 1

            print('All emails summarised successfully - now authoring summary email')
            email_message, earliest_message_datetime, latest_message_datetime = self.author_summary_email(self.messages_list)

            print('Now sending summary email to', self.gmail_account_username)
            self.send_summary_email(email_message, earliest_message_datetime, latest_message_datetime)

            end_time = datetime.now(timezone.utc)
            print("Email AI Summarisation Ended at:", end_time)
            print('Duration:', end_time - start_time)

        except Exception as e:
            print(f"An error occurred during the summarisation process: {e}")

if __name__ == "__main__":
    summarizer = EmailSummarizer()
    summarizer.run()