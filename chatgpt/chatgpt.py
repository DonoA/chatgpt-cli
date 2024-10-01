import re
import time
import openai
import os
import argparse
import pathlib

GLOBAL_ASSISTANT_FILE = pathlib.Path.home() / ".gpt/assistant_id"

def get_shell_working_file():
    return f"/tmp/{os.getppid()}"

def read_file_if_exists(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return file.read()
    return None

def write_file(file_path, content):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as file:
        file.write(content)

def create_client():
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    return client

def create_assistant(client):
    assistant_id = read_file_if_exists(GLOBAL_ASSISTANT_FILE)
    if assistant_id:
        return assistant_id

    print("Creating a new assistant...")
    my_assistant = client.beta.assistants.create(
        instructions="Blank Assistant",
        name="Default Assistant",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4o",
    )
    
    write_file(GLOBAL_ASSISTANT_FILE, my_assistant.id)
    return my_assistant.id

def create_thread(client, force_new=None):
    thread_id_file = f"{get_shell_working_file()}_thread_id"
    thread_id = read_file_if_exists(thread_id_file)
    if thread_id and not force_new:
        return thread_id
    
    response = client.beta.threads.create(
        messages=[{"role": "assistant", "content": "You are a helpful assistant."}]
    )
    thread_id = response.id
    write_file(thread_id_file, thread_id)
    return thread_id

def save_last_response(response):
    last_response_file = f"{get_shell_working_file()}_last"
    write_file(last_response_file, response)

def read_last_response():
    last_response_file = f"{get_shell_working_file()}_last"
    return read_file_if_exists(last_response_file)

def send_message(client, assistant_id, thread_id, user_message, debug=False):
    try:
        # Send the user's message to the assistant using the thread
        thread_message = client.beta.threads.messages.create(
            thread_id,
            role="user",
            content=user_message,
        )

        # Retrieve the assistant's response
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id, 
                run_id=run.id
            )
            time.sleep(0.1)

        run_msg = client.beta.threads.messages.list(
            thread_id=thread_id,
            run_id=run.id
        )
        
        if debug:
            print(run_msg)
            print()
        
        msg_txt = run_msg.data[0].content[0].text.value
        return msg_txt
    
    except Exception as e:
        print(f"Error communicating with the assistant: {e}")

def extract_code_blocks(response):
    pattern = r"```[^\n]*\n(.*?)```"
    
    # Find all matches for the pattern
    matches = re.findall(pattern, response, re.DOTALL)
    if not matches:
        return response
    else:
        return matches[0]

def print_last():
    last_response = read_last_response()
    if last_response:
        return last_response
    else:
        print("No last response found.")
        return None

def main():
    parser = argparse.ArgumentParser(description="Send a message to the GPT-4o assistant.")
    parser.add_argument("--code", action='store_true', help="Extract code blocks from the message.")
    parser.add_argument("--debug", action='store_true', help="Include debug messages")
    parser.add_argument("--new", action='store_true', help="Create a new thread starting with this message")
    parser.add_argument("--last", action='store_true', help="Print the last response again")
    parser.add_argument("message", type=str, nargs='*', help="The message to send to the assistant.")
    args = parser.parse_args()
    message = ' '.join(args.message)
    
    if args.last:
        response = print_last()
    else:
        client = create_client()
        # Get or create assistant
        assistant_id = create_assistant(client)
        # Create a new conversation thread
        thread_id = create_thread(client, force_new=args.new)

        if args.debug:
            print(f"Assistant ID: {assistant_id}")
            print(f"Thread ID: {thread_id}")
            print(f"Message To Send: {message}")
            print()

        response = send_message(client, assistant_id, thread_id, message, debug=args.debug)

    if args.code:
        response = extract_code_blocks(response)
    save_last_response(response)
    print(response)

if __name__ == "__main__":
    main()
