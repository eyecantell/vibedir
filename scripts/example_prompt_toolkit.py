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
    "suboption1": False,
    "suboption2": False
}

# Custom style for colors
style = Style.from_dict({
    'prompt': '#ffffff bold',
    'active': '#00ff00',  # Green
    'inactive': '#ff0000'  # Red
})

# Create key bindings
bindings = KeyBindings()

@bindings.add('q')
def exit_app(event):
    """Exit the application when 'q' is pressed."""
    event.app.exit(result='q')
    logging.info("Exiting via key binding (q).")

@bindings.add('b')
def back_to_menu(event):
    """Go back to parent menu when 'b' is pressed (in submenus)."""
    event.app.exit(result='b')
    logging.info("Going back via key binding (b).")

@bindings.add('h')
def show_help(event):
    """Show help menu when 'h' is pressed."""
    event.app.exit(result='h')
    logging.info("Showing help via key binding (h).")

# Numeric bindings for menu selections
for i in range(1, 10):  # Bind '1' to '9'
    @bindings.add(str(i))
    def _(event, number=str(i)):
        """Select menu option when numeric key is pressed."""
        event.app.exit(result=number)
        logging.info(f"Selected option via key binding ({number}).")

def get_help_text():
    """Return help text for the current menu."""
    return HTML(
        "Help:\n"
        "<active>[q]</active> - Quit the application\n"
        "<active>[h]</active> - Show this help\n"
        "<active>[b]</active> - Go back to parent menu (in submenus)\n"
        "<active>[1-9]</active> - Select numbered menu option\n"
        "Press <enter> key to continue..."
    )

def main_menu():
    session = PromptSession(
        multiline=False,
        completer=WordCompleter(['1', '2', 'q', 'h']),
        style=style,
        key_bindings=bindings
    )
    prompt = HTML(
        "Main Menu:\n"
        f"[1] Submenu 1 <active>[{'Active' if states['option1'] else 'Inactive'}]</active>\n"
        "[2] Immediate Action\n"
        "Press [q] to quit, [h] for help\n> "
    )
    while True:
        try:
            choice = session.prompt(prompt)
            logging.info(f"Main menu choice: {choice}")
            if choice == '1':
                if submenu1():
                    return True  # Exit program
            elif choice == '2':
                print("Executing immediate action...")
                states["option1"] = not states["option1"]
            elif choice == 'q':
                print("Exiting...")
                return True
            elif choice == 'h':
                session.prompt(get_help_text())  # Show help
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            print("Exiting via Ctrl+C...")
            return True
        except EOFError:
            print("Exiting via Ctrl+D...")
            return True

def submenu1():
    session = PromptSession(
        multiline=False,
        completer=WordCompleter(['1', '2', 'b', 'q', 'h']),
        style=style,
        key_bindings=bindings
    )
    prompt = HTML(
        "Submenu 1:\n"
        f"[1] Suboption 1 <inactive>[{'Active' if states['suboption1'] else 'Inactive'}]</inactive>\n"
        "[2] Submenu 2\n"
        "Press [b] to go back, [q] to quit, [h] for help\n> "
    )
    while True:
        try:
            choice = session.prompt(prompt)
            logging.info(f"Submenu 1 choice: {choice}")
            if choice == '1':
                print("Toggling suboption 1 state...")
                states["suboption1"] = not states["suboption1"]
            elif choice == '2':
                if submenu2():
                    return True  # Exit program
            elif choice == 'b':
                return False  # Back to main menu
            elif choice == 'q':
                print("Exiting...")
                return True
            elif choice == 'h':
                session.prompt(get_help_text())  # Show help
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            print("Exiting via Ctrl+C...")
            return True
        except EOFError:
            print("Exiting via Ctrl+D...")
            return True

def submenu2():
    session = PromptSession(
        multiline=False,
        completer=WordCompleter(['1', '2', 'b', 'q', 'h']),
        style=style,
        key_bindings=bindings
    )
    prompt = HTML(
        "Submenu 2:\n"
        f"[1] Suboption 2 <inactive>[{'Active' if states['suboption2'] else 'Inactive'}]</inactive>\n"
        "[2] Back\n"
        "Press [b] to go back, [q] to quit, [h] for help\n> "
    )
    while True:
        try:
            choice = session.prompt(prompt)
            logging.info(f"Submenu 2 choice: {choice}")
            if choice == '1':
                print("Toggling suboption 2 state...")
                states["suboption2"] = not states["suboption2"]
            elif choice in ('2', 'b'):
                return False  # Back to submenu 1
            elif choice == 'q':
                print("Exiting...")
                return True
            elif choice == 'h':
                session.prompt(get_help_text())  # Show help
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            print("Exiting via Ctrl+C...")
            return True
        except EOFError:
            print("Exiting via Ctrl+D...")
            return True

if __name__ == "__main__":
    main_menu()