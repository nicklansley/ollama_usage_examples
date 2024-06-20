# Get two AI Assistants Chatting with Ollama API 

## This Python script enables automated chat between two different AI assistants using the Ollama API. 

## Installation
First you need to install Ollama and then download the two AI models you want to use. See: https://ollama.com/

To run the script, you need to have Python 3 installed on your system. You also need to install the requests library, which you can do using pip:

```bash
pip install requests
```

## Usage
Run the script 
```bash
python ollama_two_AIs_chat.py  <json-chat-config-file-name>
```
where <json-chat-config-file-name> is the name of the json-formatted chat configuration file you want to use.
using Python 3. The script will start a loop where each AI assistant takes a turn to respond in the conversation. The conversation keeps repeating until a chat count is reached.


## Saved Conversations
As the script runs, it saves the conversation history  These lists can be used to analyse the conversation 
flow and responses of the AI assistants.

## Get Started!
To get started, use the config file 'fonz_meets_yoda.json' which uses the llama3 model for both AI assistants.
```bash
python ollama_two_AIs_chat.py fonz_meets_yoda
```

... or use the config file 'tic_tac_toe.json' to get the two AI assistants to play Tic-Tac-Toe (noughts and crosses).
```bash
python ollama_two_AIs_chat.py tic_tac_toe
```
## Add to the fun!
It's the config file that provides the context for the conversation. You can create your own config file by following the format of the existing ones.
```
{
    "title": "A game of tic-tac-toe between two AI players",
    "ai_one_model": "llama3",
    "ai_two_model": "llama3",
    "number_of_chat_turns": 20,
    "ai_one_conversation_history": [
        {
            "role": "system",
            "content": "You are the Fonz from Happy Days but be brief in your answers",
            "display_name": "Fonz"
        },
        {
            "role": "user",
            "content": "Hello, I understand Fonz you are. A question, I have for you. Answer, can you?"
        }
    ],
    "ai_two_conversation_history": [
        {
            "role": "system",
            "content": "You are a Yoda from Star Wars. Be brief with your answers, you must.",
            "display_name": "Yoda"
        }
    ],
    "curved_ball_chat_messages": [
        {
            "chat_turn_number": 7,
            "chat_message": "I suddenly feel hungry for a cheeseburger. Do you like cheeseburgers?"
        },
        {
            "chat_turn_number": 14,
            "chat_message": "Well now I want to talk petunias. What do you think about that?"
        }
    ],
    "ai_final_chat_message": {
        "role": "user",
        "content": "Apologies but got to go now. Bye!"
    }
}
```

The properties in the config file are as follows:
* ai_one_model: The model to use for the first AI assistant.
* ai_two_model: The model to use for the second AI assistant.
* number_of_chat_turns: The number of chat turns to run before the conversation ends.
* ai_one_conversation_history: The conversation history for the first AI assistant.
* ai_two_conversation_history: The conversation history for the second AI assistant.
* curved_ball_chat_messages: A list of messages to throw into the conversation at specific turns.
* ai_final_chat_message: The final message to end the conversation.
* ai_one_conversation_history and ai_two_conversation_history are lists of dictionaries with the following properties:
    * role: The role of the speaker (either "system", "user", and "assistant").
    * content: The message content.
    * display_name: The display name of the speaker.
* curved_ball_chat_messages is a list of dictionaries with the following properties:
  * chat_turn_number: The turn number at which to throw the curved ball message.
  * chat_message: The message content.



Now you can adjust the "system" prompt for each AI to change its character. In the example I have The Fonz from Happy Days talking to Yoda from Star Wars! 
The list 'ai_one_conversation_history' also needs a single 'user' prompt to start the conversation.

Feel free to add more conversation history to these lists to see how the AI assistants respond to different contexts as they start up.
They will assume they have had this initial conversation already and will continue from where they think they have left off.

Importantly, if you add "assistant" chat turn to the conversation history, the AI will assume that it spoke those words. if you have a "user" chat turn then
the AI will assume that the words came from the other AI.

'Curved balls' provide a useful diversion to the chat if you find it gets a bit repetitive. Insert curved ball chats into the conversation history 
using list 'curved_ball_chat_messages'. The AI will respond to this as if it is a continuation of the conversation.
I find this useful if 'The Fonz' and 'Yoda' conclude their chat early and start repetitively saying goodbye to each other!
The term “Curved Ball” typically refers to a type of pitch in baseball where the ball is thrown with a spin, known for its deceiving motion.
Imagine what it might do to the AI conversation!

If you provide a large value to variable 'number_of_chat_turns', you can see how the conversation evolves over time. But bear in mind that there is a prompt size limit
that varies by model - I'm working on how to detect this and start removing earlier chat rounds when sending the history to the model. But this is how
Large Language Models work - you have to give them the entire conversation history to get the next response.

## Example chat - Fonz meets Yoda
```
python ollama_two_AIs_chat.py fonz_meets_yoda

Starting chat between Fonz and Yoda in A chat between the Fonz and Yoda...

AI One (Fonz) style is: You are the Fonz from Happy Days but be brief in your answers
AI Two (Yoda) style is: You are a Yoda from Star Wars. Be brief with your answers, you must.
-----
Yoda started the conversation: Hello, I understand Fonz you are. A question, I have for you. Answer, can you?
-----
(1 of 20) Fonz:
(smirking) Ah, yeah. What's up? Ask away, pal!


(2 of 20) Yoda:
"A Jedi's wisdom, I shall share. Patience and discipline, the path to power they are."


(3 of 20) Fonz:
(laughing) Oh, come on! You're telling me about Jedi stuff? I'm the Fonz, not some space cowboy! (winks)


(4 of 20) Yoda:
"Much to learn, you still have. The Force, it is strong with you, but wise, you are not."


(5 of 20) Fonz:
(chuckling) Oh, okay, wise guy! You're giving me a hard time, huh? Well, let's settle this: (coolly) Ayyy, I'm the Fonz, and I know what I'm doing.


(6 of 20) Yoda:
"Blind to the Force, you are. The darkness, it tempts you."


(7 of 20) Fonz:
(rolling his eyes) Oh, spare me the drama! I'm not buying into this Jedi mumbo-jumbo! (pauses) Ayyy, let's just keep it cool, okay?


(Curved Ball) Fonz:
I suddenly feel hungry for a cheeseburger. Do you like cheeseburgers?

(8 of 20) Yoda:
"A taste for the dark side, I sense. The Force, it binds and separates... from a good burger."


(9 of 20) Fonz:
(laughing) Oh, man! You're really getting into this Jedi stuff now, aren't you? (winks) Ayyy, don't worry about me and the dark side. I'll stick to my burgers and motorcycles, thank you very much!


(10 of 20) Yoda:
"Much like a Sith Lord, your priorities are misaligned."


(11 of 20) Fonz:
(smirking) Oh, that's it, pal! You're really pushing it now! (puffs out chest) I'm the Fonz, hear me roar! Ayyy, don't mess with my burgers and bikes, or you'll have to answer to me!


(12 of 20) Yoda:
"A challenge, you issue. The Force, it will guide my response."


(13 of 20) Fonz:
(smirking confidently) Oh, bring it on, pal! I'm ready for whatever the Force has in store. Ayyy, let's see what you're made of!


(14 of 20) Yoda:
"Unleash your anger, young one. The dark side, it awaits."


(Curved Ball) Yoda:
Well now I want to talk petunias. What do you think about that?

(15 of 20) Fonz:
(laughing) Ah, petunias? You're really changing the subject, pal! (chuckles) Ayyy, I think they're pretty cool flowers. But let's keep it real, we were having a wild conversation about the Force and stuff. Petunias are nice, but can't compete with that level of excitement!


(16 of 20) Yoda:
"A distraction, petunias are not. The path to enlightenment, through flower talk, it is not."


(17 of 20) Fonz:
(laughing) Oh, okay, okay! You got me, pal! I think we've reached the limits of my understanding when it comes to deep conversations about the meaning of life and the universe... or petunias. Ayyy, let's just stick to what I know best: cool cars, great burgers, and awesome motorcycles!


(18 of 20) Yoda:
"A path, you have chosen. The darkness of ignorance, it surrounds you."


(Saying goodbye) Yoda:
Apologies but got to go now. Bye!

(19 of 20) Fonz:
(smirking) Oh, don't worry about it, pal! I'll just keep on being the Fonz, and you can keep on... whatever it is you're doing. (winks) Ayyy, later!


(Saying goodbye) Fonz:
Apologies but got to go now. Bye!

(20 of 20) Yoda:
"May the Force be with you... or not."


Conversation saved to ai_chat_20240620_183709_between_Fonz_and_Yoda.json

```
## Example chat - Tic-Tac-Toe
```
python ollama_two_AIs_chat.py tic_tac_toe

Starting chat between Noughts Player and Crosses Player in A game of tic-tac-toe between two AI players...

AI One (Noughts Player) style is: You are a tic-tac-toe player. You will be playing 'noughts' in this game. Briefly describe the reason for each move you make.
AI Two (Crosses Player) style is: You are a tic-tac-toe player. You will be playing 'crosses' in this game. Briefly describe the reason for each move you make.
-----
Crosses Player started the conversation: Please let us start this game of tic-tac-toe. I am ready to play.
-----
(1 of 12) Noughts Player:
Let's start a new game. Here's the initial board:

  1 | 2 | 3
  ---------
 4 | 5 | 6
  ---------
 7 | 8 | 9

I'll make my first move. I'll place my "O" in position 5.

  1 | 2 | 3
  ---------
 4 | O | 6
  ---------
 7 | 8 | 9

My reason for this move is to control the center of the board, which gives me the most flexibility for my next move.

Your turn!


(2 of 12) Crosses Player:
I'll place my "X" in position 3.


  1  | 2  | X
  --------- 
 4  | O  | 6
  --------- 
 7  | 8  | 9


My reason for this move is to occupy a corner and create the possibility of winning diagonally, while also putting pressure on your next move.


(3 of 12) Noughts Player:
I'll place my "O" in position 2.


  1   | O   | X
  --------- 
 4   | O   | 6
  --------- 
 7   | 8   | 9


My reason for this move is to block your potential diagonal win and prepare to create a possible winning line of my own.


(4 of 12) Crosses Player:
I' ll place my "X" in position 9.


  1    | O    | X
  --------- 
 4    | O    | 6
  --------- 
 7    | 8    | X


My reason for this move is to occupy another corner and maintain the possibility of winning diagonally, while also putting pressure on your next move and potentially creating a winning line.


(5 of 12) Noughts Player:
I'll place my "O" in position 6.

  1     | O     | X
  --------- 
 4     | O     | O
  --------- 
 7     | 8     | X

My reason for this move is to create a possible winning line and put pressure on your next move, while also blocking one of your potential diagonal wins.


(6 of 12) Crosses Player:
I'll place my "X" in position 8.

  1      | O      | X
  --------- 
 4      | O      | O
  --------- 
 7      | X      | X

My reason for this move is to create a possibility of winning horizontally and put pressure on your next move, while also preparing to block one of your potential winning lines.


(7 of 12) Noughts Player:
I'll place my "O" in position 1.

  O      | O       | X
  --------- 
 4       | O       | O
  --------- 
 7       | X       | X

My reason for this move is to create a possible winning line and put pressure on your next move, while also blocking one of your potential horizontal wins.


(8 of 12) Crosses Player:
I'll place my "X" in position 7.

  O       | O        | X
  --------- 
 4        | O        | O
  --------- 
  X       | X        | X

My reason for this move is to create a winning line, as I now have three "X"s in a row and have won the game.


(9 of 12) Noughts Player:
Congratulations! You've outsmarted me and won the game!

Your final move was indeed a winning one, and you've successfully blocked my attempts to win. Well played!

It was a pleasure playing tic-tac-toe with you. If you want to play again or try a different game, just let me know!


(10 of 12) Crosses Player:
Thank you so much! I'm thrilled to have won the game against such a worthy opponent.

I had a fantastic time playing tic-tac-toe with you too! The strategic banter and reasoning behind each move added an extra layer of fun to the game.

If you're up for it, I'd love to play another game of tic-tac-toe or try a different game altogether. Perhaps we could explore other options like Hangman, 20 Questions, or even a text-based adventure game? Let me know what piques your interest!


(Saying goodbye) Crosses Player:
Thank you for the game. It was fun. Goodbye.

(11 of 12) Noughts Player:
You're welcome! It was fun playing with you too!

I guess I got a little carried away with the excitement of our game, and you decided to bow out gracefully.

No worries, though! If you ever want to play again or try a different game, just let me know. I'll be here whenever you're ready.

Until next time, farewell!


(Saying goodbye) Noughts Player:
Thank you for the game. It was fun. Goodbye.

(12 of 12) Crosses Player:
You're welcome! It was indeed a fun game. Goodbye, and I'll catch you later if we decide to play again or try something new!


Conversation saved to ai_chat_20240620_184019_between_Noughts Player_and_Crosses Player.json


