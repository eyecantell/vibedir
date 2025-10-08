import logging
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings

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

# Create key bindings
bindings = KeyBindings()

@bindings.add('x')
@bindings.add('q')
def _(event):
    """Exit the application when 'x' or 'q' is pressed."""
    event.app.exit(result='exit')  # Set result to signal exit
    logging.info("Exiting via key binding (x or q).")

def main_menu():
    session = PromptSession(
        multiline=False,
        completer=WordCompleter(['1', '2', '3', 'x', 'q']),  # Include x, q in completer
        style=style,
        key_bindings=bindings
    )
    while True:
        try:
            choice = session.prompt(HTML(
                "Main Menu:\n"
                f"1. Option with Submenu <active>[{'Active' if states['option1'] else 'Inactive'}]</active>\n"
                "2. Immediate Action\n"
                "3. Exit (or press 'x'/'q')\n> "
            ))
            logging.info(f"Main menu choice: {choice}")
            if choice == '1':
                if submenu():
                    print("Exiting from submenu...")
                    return True  # Signal program exit
            elif choice == '2':
                print("Executing immediate action...")
                states["option1"] = not states["option1"]  # Toggle state
            elif choice in ('3', 'x', 'q', 'exit'):  # Handle numeric and key inputs
                print("Exiting...")
                return True  # Signal program exit
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            print("Exiting via Ctrl+C...")
            return True  # Signal program exit
        except EOFError:  # Handle Ctrl+D
            print("Exiting via Ctrl+D...")
            return True  # Signal program exit

def submenu():
    session = PromptSession(
        multiline=False,
        completer=WordCompleter(['1', '2', 'x', 'q']),  # Include x, q in completer
        style=style,
        key_bindings=bindings
    )
    while True:
        try:
            choice = session.prompt(HTML(
                "Submenu:\n"
                f"1. Suboption 1 <inactive>[{'Active' if states['suboption1'] else 'Inactive'}]</inactive>\n"
                "2. Back (or press 'x'/'q' to exit)\n> "
            ))
            logging.info(f"Submenu choice: {choice}")
            if choice == '1':
                print("Toggling suboption state...")
                states["suboption1"] = not states["suboption1"]
            elif choice == '2':
                return False  # Normal return to main menu
            elif choice in ('x', 'q', 'exit'):  # Allow exit from submenu
                return True  # Signal to exit main menu
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            print("Exiting via Ctrl+C from submenu...")
            return True  # Signal program exit
        except EOFError:
            print("Exiting via Ctrl+D from submenu...")
            return True  # Signal program exit

if __name__ == "__main__":
    main_menu()