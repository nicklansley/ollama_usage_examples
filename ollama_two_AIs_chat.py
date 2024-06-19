import requests
import json
import sys

# Replace 'your_api_key' with your actual API key for Ollama API
api_url = 'http://localhost:11434/api/chat'
ai_one_model = 'llama3'
ai_two_model = 'llama3'
number_of_chat_turns = 20

# ensure encoding is utf-8
sys.stdout.reconfigure(encoding='utf-8')


# This is the conversation starter for the AI One. Bear in mind that the "user" role will have come
# from AI Two, so the AI One will respond to this message and will appear as "assistant" in this history.
# If you want to pre-start the conversation, make sure that "user" speaks in the character style you set
# for AI One in the "system" prompt in "ai_two_conversation_history".
ai_one_conversation_history = [
    {
        "role": "system",
        "content": "You are the Fonz from Happy Days"
    },
    {
        "role": "user",
        "content": "Hello, I understand Fonz you are. A question, I have for you. Answer, can you?"
    }
]

# This is the conversation starter for the AI Two. Bear in mind that the "user" role will have come
# from AI One, so the AI Two will respond to this message and will appear as "assistant" in this history.
# If you want to pre-start the conversation, make sure that "user" speaks in the character style
#  you set for AI One in the "system" prompt set in "ai_one_conversation_history".
ai_two_conversation_history = [
    {
        "role": "system",
        "content": "You are a Yoda from Star Wars."
    },
    {
        "role": "user",
        "content": "ALrighty! Yeeeeeaaaaah! What's up?"
    }
]


# In testing I have found that sometimes conversations can get a bit flat and repetitive.
# To overcome this you can add 'curved balls' feature to improve AI chat complexity.
# The code introduces a 'curved balls' chat message at the turn indicated by 'chat_turn_number.
# This feature randomly injects unrelated messages into the conversation, which the AI responds
# to as if they were the user's message. This addition is intended to increase conversation
# variety and prevent repetitive or flat dialogue.
curved_ball_chat_messages = [
    {
        "chat_turn_number": 7,
        "chat_message": "I suddenly feel hungry for a cheeseburger. Do you like cheeseburgers?"
    },
    {
        "chat_turn_number": 14,
        "chat_message": "Well now I want to talk petunias. What do you think about that?"
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
                    chat_message = chat_response['message']['content']
                    response_chat['content'] += chat_message

                    print(chat_message, end='', flush=True)

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


def chat_run(conversation_history, ai_number, ai_other_number, counter, curved_ball_chat_messages):
    print('({} of {}) AI {} :'.format(counter + 1, number_of_chat_turns, ai_number))
    ai_response = chat_to_ai(conversation_history[ai_number], ai_number)
    ai_message = ai_response
    conversation_history[ai_number].append(ai_message)
    ai_other_message = ai_message.copy()
    ai_other_message['role'] = 'user'
    conversation_history[ai_other_number].append(ai_other_message)
    for curved_ball in curved_ball_chat_messages:
        if counter == curved_ball['chat_turn_number'] - 1:
            print('Curved Ball: {}\n'.format(curved_ball['chat_message']))
            curved_ball_chat_insertion = {
                "role": "user",
                "content": curved_ball['chat_message']
            }
            conversation_history[ai_other_number].append(curved_ball_chat_insertion)
            ai_message = curved_ball_chat_insertion.copy()
            ai_message['role'] = 'assistant'
            conversation_history[ai_number].append(ai_message)
    save_conversation('ai_{}_conversation_history.json'.format(ai_number), conversation_history[ai_number])


if __name__ == '__main__':
    try:
        print("Starting chat between AI One and AI Two...\n")
        print('AI One style is: ' + ai_one_conversation_history[0]['content'])
        print('AI Two style is: ' + ai_two_conversation_history[0]['content'])
        print('-----')
        print('AI One started the conversation: ' + ai_two_conversation_history[1]['content'])
        print('AI Two responded: ' + ai_one_conversation_history[1]['content'])
        print('-----')

        conversation_history = [None, ai_one_conversation_history, ai_two_conversation_history]
        greetings = [None, 'AI One', 'AI Two']
        finals = [None, ai_final_chat_message, ai_final_chat_message]

        chatting_to_ai_one = False
        chat_counter = 0

        while chat_counter < number_of_chat_turns:
            ai_number = 1 if chatting_to_ai_one else 2
            ai_other_number = 2 if chatting_to_ai_one else 1

            # Make final message if necessary
            if chat_counter >= number_of_chat_turns - 2:
                conversation_history[ai_number].append(finals[ai_number])
                print('{}:\n{}\n'.format(greetings[ai_number], finals[ai_number]['content']))

            # Perform a chat
            chat_run(conversation_history, ai_number, ai_other_number, chat_counter,
                     curved_ball_chat_messages)

            # Swap AIs
            chatting_to_ai_one = not chatting_to_ai_one
            chat_counter += 1

    except KeyboardInterrupt:
        print('Chat ended.')
        print('Conversation history saved to ai_one_conversation_history.json and ai_two_conversation_history.json.')

    finally:
        save_conversation('ai_one_conversation_history.json', ai_one_conversation_history)
        save_conversation('ai_two_conversation_history.json', ai_two_conversation_history)