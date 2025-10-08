import logging
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

# Setup logging for debugging (optional, can be removed)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# State tracking for menu options
states = {
    "option1": True,  # Active/Inactive toggle
    "suboption1": False
}

# Custom style for colors
style = Style.from_dict({
    'prompt': '#ffffff bold',
    'active': '#00ff00',  # Green
    'inactive': '#ff0000'  # Red
})

def main_menu():
    session = PromptSession(multiline=False, completer=WordCompleter(['1', '2', '3']), style=style)
    while True:
        try:
            choice = session.prompt(HTML(
                "Main Menu:\n"
                f"1. Option with Submenu [{'<active>Active</active>' if states['option1'] else '<inactive>Inactive</inactive>'}]\n"
                "2. Immediate Action\n"
                "3. Exit\n> "
            ))
            logging.info(f"Main menu choice: {choice}")
            if choice == '1':
                submenu()
            elif choice == '2':
                print("Executing immediate action...")
                states["option1"] = not states["option1"]  # Toggle state
            elif choice == '3':
                print("Exiting...")
                break
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            print("Exiting...")
            break

def submenu():
    session = PromptSession(multiline=False, completer=WordCompleter(['1', '2']), style=style)
    while True:
        try:
            choice = session.prompt(HTML(
                "Submenu:\n"
                f"1. Suboption 1 [{'<active>Active</active>' if states['suboption1'] else '<inactive>Inactive</inactive>'}]\n"
                "2. Back\n> "
            ))
            logging.info(f"Submenu choice: {choice}")
            if choice == '1':
                print("Toggling suboption state...")
                states["suboption1"] = not states["suboption1"]
            elif choice == '2':
                break
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main_menu()