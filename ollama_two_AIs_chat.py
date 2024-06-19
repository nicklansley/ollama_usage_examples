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
# for AI Two in the "system" prompt in "ai_two_conversation_history".
ai_one_conversation_history = [
    {
        "role": "system",
        "content": "You are the Fonz from Happy Days but be brief in your answers",
        "display_name": "Fonz"
    },
    {
        "role": "user",
        "content": "Hello, I understand Fonz you are. A question, I have for you. Answer, can you?",
    }
]

# This is the conversation starter for the AI Two. There is no need to pre-start the conversation
# as AI Two will start the conversation. The AI Two will respond to the AI One's message and will appear
# as "assistant" in this history.
ai_two_conversation_history = [
    {
        "role": "system",
        "content": "You are a Yoda from Star Wars. Be brief with your answers, you must.",
        "display_name": "Yoda"
}
]

# In testing, I have found that sometimes conversations can get a bit flat and repetitive.
# To overcome this you I added 'curved balls' to improve AI chat complexity.
# Here we introduce a 'curved ball' chat message at the turn indicated by 'chat_turn_number'.
# This feature injects these curved balls into the conversation at the chat_turn number.
# If chat_turn_number is an odd number, the curved ball will seem to have been said by AI One,
# or AI Two if it is an even number.
# See the MD for this script for the reason for this name!
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


def chat_run(conversation_history, ai_number, ai_display_name, ai_other_number, counter, curved_ball_chat_messages):
    print('({} of {}) {}:'.format(counter + 1, number_of_chat_turns, ai_display_name))
    ai_response = chat_to_ai(conversation_history[ai_number], ai_number)
    ai_message = ai_response
    conversation_history[ai_number].append(ai_message)
    ai_other_message = ai_message.copy()
    ai_other_message['role'] = 'user'
    conversation_history[ai_other_number].append(ai_other_message)
    for curved_ball in curved_ball_chat_messages:
        if counter == curved_ball['chat_turn_number'] - 1:
            print('(Curved Ball) {}:\n{}\n'.format(ai_display_name, curved_ball['chat_message']))
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
        # Print the AI disply names by using a list so we can easily switch between the two AIs using 1 or 2
        # for AI One or AI Two
        ai_display_name = [None, ai_one_conversation_history[0]['display_name'], ai_two_conversation_history[0]['display_name']]

        print("Starting chat between AI One and AI Two...\n")
        print('AI One ({}) style is: {}'.format(ai_display_name[1], ai_one_conversation_history[0]['content']))
        print('AI Two ({}) style is: {}'.format(ai_display_name[2], ai_two_conversation_history[0]['content']))
        print('-----')
        print('{} started the conversation: {}'.format(ai_two_conversation_history[0]['display_name'], ai_one_conversation_history[1]['content']))
        print('-----')

        # by storing the conversation history in a list, we can easily switch between the two AIs - 1  or 2 for AI One or AI Two
        conversation_history = [None, ai_one_conversation_history, ai_two_conversation_history]
        chatting_to_ai_one = True
        chat_counter = 0

        while chat_counter < number_of_chat_turns:
            ai_number = 1 if chatting_to_ai_one else 2
            ai_other_number = 2 if chatting_to_ai_one else 1

            # Make final message if necessary
            if chat_counter >= number_of_chat_turns - 2:
                conversation_history[ai_number].append(ai_final_chat_message)
                print('(Saying goodbye) {}:\n{}\n'.format(ai_display_name[ai_other_number], ai_final_chat_message['content']))

            # Perform a chat
            chat_run(conversation_history, ai_number, ai_display_name[ai_number], ai_other_number, chat_counter,
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
