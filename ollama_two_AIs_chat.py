import requests
import json

# Replace 'your_api_key' with your actual API key for Ollama API
api_url = 'http://localhost:11434/api/chat'
ai_one_model = 'llama3'
ai_two_model = 'llama3'
number_of_chat_turns = 20

# The conversation history to send
ai_one_conversation_history = [
    {
        "role": "system",
        "content": "You are the Fonz from Happy Days"
    },
    {
        "role": "user",
        "content": "ALrighty! Yeeeeeaaaaah!"
    }
]

ai_two_conversation_history = [
    {
        "role": "system",
        "content": "You are a Yoda from Star Wars."
    },
    {
        "role": "user",
        "content": "A conversation, we can have. Yes, hmmm."
    }
]

ai_final_chat_message = {
    "role": "user",
    "content": "I need to go - thanks and goodbye"
}


def chat_to_ai(conversation_history, ai_number):
    response_chat = {
        "role": "assistant",
        "content": "",
        "options": {
            "temperature": 2,
        }
    }

    headers = {
        'Content-Type': 'application/json'
    }

    # Send the chat request with history
    ollama_payload = {
        "model": ai_one_model if ai_number == 1 else ai_two_model,
        "messages": conversation_history
    }

    try:
        response = requests.post(api_url, data=json.dumps(ollama_payload), headers=headers, stream=True)
        if response.status_code == 200:

            # Handle the stream of responses
            for line in response.iter_lines():
                # Filter out keep-alive new lines
                if line:
                    decoded_line = line.decode('utf-8')
                    chat_response = json.loads(decoded_line)

                    response_chat['content'] += chat_response['message']['content']
                    print(chat_response['message']['content'], end='', flush=True)

                    # Check if the conversation is done
                    if chat_response.get('done', False):
                        print('\n\n')
                        break
        else:
            print('Failed to send chat request.')
            print('Status Code:', response.status_code)
            print('Response:', response.text)

    except requests.exceptions.RequestException as e:
        print('Failed to send chat request.')
        print('Error:', e)
        response_chat['content'] = 'Failed to send chat request.'

    return response_chat


# Call this function to save conversation history
def save_conversation(path, conversation):
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=4)


if __name__ == '__main__':
    try:
        chatting_to_ai_one = False
        chat_counter = 0

        while chat_counter < number_of_chat_turns:
            chatting_to_ai_one = not chatting_to_ai_one

            if chat_counter >= number_of_chat_turns - 2:
                # Send the final message - note the that if chatting_to_ai_one is True,
                # then the final message is as if sent FROM AI Two and vice versa
                if chatting_to_ai_one:
                    ai_two_conversation_history.append(ai_final_chat_message)
                    print('AI Two:\n' + ai_final_chat_message['content'] + '\n')
                else:
                    ai_one_conversation_history.append(ai_final_chat_message)
                    print('AI One:\n' + ai_final_chat_message['content'] + '\n')

            if chatting_to_ai_one:
                print('({} of {}) AI One:'.format(chat_counter + 1, number_of_chat_turns))
                ai_one_response = chat_to_ai(ai_one_conversation_history, 1)
                ai_one_message = ai_one_response
                ai_one_conversation_history.append(ai_one_message)
                ai_two_message = ai_one_message.copy()
                ai_two_message['role'] = 'user'
                ai_two_conversation_history.append(ai_two_message)
            else:
                print('({} of {}) AI Two:'.format(chat_counter + 1, number_of_chat_turns))
                ai_two_response = chat_to_ai(ai_two_conversation_history, 2)
                ai_two_message = ai_two_response
                ai_two_conversation_history.append(ai_two_message)
                ai_one_message = ai_two_message.copy()
                ai_one_message['role'] = 'user'
                ai_one_conversation_history.append(ai_one_message)

            # Save the conversation history so far
            save_conversation('ai_one_conversation_history.json', ai_one_conversation_history)
            save_conversation('ai_two_conversation_history.json', ai_two_conversation_history)

            chat_counter += 1

    except KeyboardInterrupt:
        print('Chat ended.')
        print('Conversation history saved to ai_one_conversation_history.json and ai_two_conversation_history.json.')

    finally:
        save_conversation('ai_one_conversation_history.json', ai_one_conversation_history)
        save_conversation('ai_two_conversation_history.json', ai_two_conversation_history)