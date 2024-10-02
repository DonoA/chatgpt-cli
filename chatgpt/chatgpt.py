import re
import sys
import time
import openai
import os
import argparse
import pathlib

GLOBAL_ASSISTANT_FILE = pathlib.Path.home() / ".gpt/assistant_id"
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("CHATGPT_CLI_MODEL", default="gpt-4o")
MODEL_INIT_MESSAGE = os.getenv("CHATGPT_CLI_INIT", 
    default="Assist a programmer with their code.")

class OpenAIClient:
    def __init__(self):
        self.client = None

    def get_shell_working_file(self):
        return f"/tmp/{os.getppid()}"

    def read_file_if_exists(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                return file.read()
        return None

    def write_file(self, file_path, content):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            file.write(content)

    def get_client(self):
        if self.client is None:
            self.client = openai.OpenAI(
                api_key=API_KEY,
            )
        return self.client

    def create_assistant(self, force_new=False):
        assistant_id = self.read_file_if_exists(GLOBAL_ASSISTANT_FILE)
        if assistant_id and not force_new:
            return assistant_id

        print("Creating a new assistant...")
        my_assistant = self.get_client().beta.assistants.create(
            instructions=MODEL_INIT_MESSAGE,
            name="Default Assistant",
            tools=[{"type": "code_interpreter"}],
            model=MODEL_NAME,
        )
        
        self.write_file(GLOBAL_ASSISTANT_FILE, my_assistant.id)
        return my_assistant.id

    def create_thread(self, force_new=False):
        thread_id_file = f"{self.get_shell_working_file()}_thread_id"
        thread_id = self.read_file_if_exists(thread_id_file)
        if thread_id and not force_new:
            return thread_id
        
        response = self.get_client().beta.threads.create(
            messages=[{"role": "assistant", "content": "You are a helpful assistant."}]
        )
        thread_id = response.id
        self.write_file(thread_id_file, thread_id)
        return thread_id

    def save_last_response(self, response):
        last_response_file = f"{self.get_shell_working_file()}_last"
        self.write_file(last_response_file, response)

    def read_last_response(self):
        last_response_file = f"{self.get_shell_working_file()}_last"
        return self.read_file_if_exists(last_response_file)

    def send_message(self, assistant_id, thread_id, attached_file, user_message, debug=False):
        try:
            attachments = None
            if attached_file is not None:
                attachments = [
                    {
                        "file_id": attached_file, 
                        "tools": [{"type": "code_interpreter"}]
                    }
                ]
            # Send the user's message to the assistant using the thread
            thread_message = self.get_client().beta.threads.messages.create(
                thread_id,
                role="user",
                content=user_message,
                attachments=attachments
            )

            # Retrieve the assistant's response
            run = self.get_client().beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )
            while run.status != "completed":
                run = self.get_client().beta.threads.runs.retrieve(
                    thread_id=thread_id, 
                    run_id=run.id
                )
                time.sleep(0.1)

            run_msg = self.get_client().beta.threads.messages.list(
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

    def attach_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        with open(file_path, "rb") as file:
            response = self.get_client().files.create(
                file=file,
                purpose="assistants"
            )

        file_id = response.id
        last_fileid_file = f"{self.get_shell_working_file()}_last_file"
        self.write_file(last_fileid_file, file_id)
        return file_id
        

    def extract_code_blocks(self, response):
        pattern = r"```[^\n]*\n(.*?)```"
        
        # Find all matches for the pattern
        matches = re.findall(pattern, response, re.DOTALL)
        if not matches:
            return response
        else:
            return matches[0]

    def get_last(self):
        last_response = self.read_last_response()
        if last_response:
            return last_response
        else:
            return "No last response found."

    def get_last_file(self):
        last_fileid_file = f"{self.get_shell_working_file()}_last_file"
        return self.read_file_if_exists(last_fileid_file)
    
    def handle(self, parser, args):
        message = ' '.join(args.message)
        
        if args.file is None:
            attached_file = None
        elif args.file.lower() == 'last':
            attached_file = self.get_last_file()
            if attached_file is None:
                print("No previous file to attach")
        else:
            attached_file = self.attach_file(args.file)
            print(f"File attached as {attached_file}")

        response = None
        if args.last:
            response = self.get_last()
        elif message != "":
            # Get or create assistant
            assistant_id = self.create_assistant(force_new=args.new)
            # Create a new conversation thread
            thread_id = self.create_thread(force_new=args.new)

            if args.debug:
                print(f"Assistant ID: {assistant_id}")
                print(f"Thread ID: {thread_id}")
                print(f"Message To Send: {message}")
                print(f"Attached File: {attached_file}")
                print()

            response = self.send_message(
                                    assistant_id, 
                                    thread_id, 
                                    attached_file, 
                                    message, 
                                    debug=args.debug)

        if args.code:
            response = self.extract_code_blocks(response)
        
        if response:
            self.save_last_response(response)
            print(response)

def main():
    parser = argparse.ArgumentParser(description="Send a message to the GPT-4o assistant.")
    parser.add_argument("--code", action='store_true', help="Extract code blocks from the message.")
    parser.add_argument("--debug", action='store_true', help="Include debug messages")
    parser.add_argument("--new", action='store_true', help="Create a new thread starting with this message")
    parser.add_argument("--last", action='store_true', help="Print the last response again")
    parser.add_argument("--file", type=str, help="The file to send to the assistant, " + 
                        "if 'last' is provided, the last file will be used.")
    parser.add_argument("message", type=str, nargs='*', help="The message to send to the assistant.")
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    client = OpenAIClient()
    client.handle(parser, args)

if __name__ == "__main__":
    main()
