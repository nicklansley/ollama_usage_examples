import requests
import json

# Replace 'your_api_key' with your actual API key for Ollama API
api_url = 'http://localhost:11434/api/chat'
ai_one_model = 'llama3'
ai_two_model = 'llama3'
number_of_chat_turns = 20

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


if __name__ == '__main__':
    try:
        print("Starting chat between AI One and AI Two...\n")
        print('AI One style is: ' + ai_one_conversation_history[0]['content'])
        print('AI Two style is: ' + ai_two_conversation_history[0]['content'])
        print('-----')

        # Remember that at start up, the first words of the AI appear as 'user' in the conversation history
        # of the other AI. So, the first message of AI One is actually the first message of AI Two and vice versa.
        print('AI One started the conversation: ' + ai_two_conversation_history[1]['content'])
        print('AI Two responded: ' + ai_one_conversation_history[1]['content'])
        print('-----')

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
                # curved ball check
                for curved_ball in curved_ball_chat_messages:
                    if chat_counter == curved_ball['chat_turn_number'] - 1:
                        print('Curved Ball: {}\n'.format(curved_ball['chat_message']))
                        curved_ball_chat_insertion = {
                            "role": "user",
                            "content": curved_ball['chat_message']
                        }
                        ai_two_conversation_history.append(curved_ball_chat_insertion)
                        ai_one_message = curved_ball_chat_insertion.copy()
                        ai_one_message['role'] = 'assistant'
                        ai_one_conversation_history.append(ai_one_message)
            else:
                print('({} of {}) AI Two:'.format(chat_counter + 1, number_of_chat_turns))
                ai_two_response = chat_to_ai(ai_two_conversation_history, 2)
                ai_two_message = ai_two_response
                ai_two_conversation_history.append(ai_two_message)
                ai_one_message = ai_two_message.copy()
                ai_one_message['role'] = 'user'
                ai_one_conversation_history.append(ai_one_message)
                # curved ball check
                for curved_ball in curved_ball_chat_messages:
                    if chat_counter == curved_ball['chat_turn_number'] - 1:
                        print('Curved Ball: {}\n'.format(curved_ball['chat_message']))
                        curved_ball_chat_insertion = {
                            "role": "user",
                            "content": curved_ball['chat_message']
                        }
                        ai_one_conversation_history.append(curved_ball_chat_insertion)
                        ai_two_message = curved_ball_chat_insertion.copy()
                        ai_two_message['role'] = 'assistant'
                        ai_two_conversation_history.append(ai_two_message)

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