ChatGPT CLI
===
An unofficial tool for creating and interacting with OpenAI assistants and threads on the command line. Each execution of the command within the same terminal will continue to add to the same thread.

## Setup
The tool depends on an active OpenAI API key. This can be generated in https://platform.openai.com/api-keys. Each request will charge your OpenAI account which will need to be configured with credits before the tool can be used. Billing is set up on https://platform.openai.com/settings/organization/billing/overview.

Once you have obtained an OpenAI API key, export it in your environment under `OPENAI_API_KEY`

Personally, I prefer a smaller prefix for my conversations. I add the following alias to my .zshrc

```
alias gpt='chatgpt'
```

## Usage

```
usage: chatgpt [-h] [--code] [--debug] [--new] [--last] message [message ...]

Send a message to the GPT-4o assistant.

positional arguments:
  message     The message to send to the assistant.

options:
  -h, --help  show this help message and exit
  --code      Extract code blocks from the message.
  --debug     Include debug messages
  --new       Create a new thread starting with this message
  --last      Print the last response again
```

Example usage with continued thread
```
$ chatgpt Call me John from now on
Sure thing, John! How can I assist you today?
$ chatgpt What is my name
Your name is John. How can I help you, John?
```

### Last
The last flag allows you to re-print the last response without re-generating it (which might not result in the same result). This is particularly useful when combined with the `--code` flag which will strip away the rest of the message and only return the first code block. Tripple backticks have been replaced with double for formatting reasons

```
$ chatgpt Write a python script to print the time 
Sure, John! Here's a simple Python script to print the current time:

``python
from datetime import datetime

def print_current_time():
    # Get the current date and time
    now = datetime.now()
    
    # Format the time as a string
    current_time = now.strftime("%H:%M:%S")
    
    # Print the current time
    print("Current Time is:", current_time)

# Call the function to print the current time
print_current_time()
``

You can save this script to a file (e.g., `print_time.py`) and run it using your Python interpreter.

When you run the script, it will output the current time in the format `HH:MM:SS`.
$ chatgpt --last --code | python3
Current Time is: 21:55:34
```

### New
Internally, the script stores the current conversation ID attached to the parent processes ID (in most cases this is the shell executing the command). Sometimes it's nice to start over without killing the terminal and restarting it. In this case, `--new` can be used:
```
$ chatgpt --debug Call me steve from now on      
Assistant ID: asst_eQjFYpMxSW0GlLJkTLo0GkxC
Thread ID: thread_P5owk1MmVXJ8C6TGRZ6eiW1R
Message To Send: Call me steve from now on

Got it, Steve! How can I assist you today?
$ chatgpt --new --debug What is my name           
Assistant ID: asst_eQjFYpMxSW0GlLJkTLo0GkxC
Thread ID: thread_elSUCvucgM8AcfP1aP2bRxRd
Message To Send: What is my name

You haven't told me your name yet. How can I address you?
```

## Developing
Develop in a venv:
```
python3 -m venv .
source bin/activate
pip3 install -e .
```

This will install the module and make it executable with the command `chatgpt`

