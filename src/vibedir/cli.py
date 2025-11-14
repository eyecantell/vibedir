import logging
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings

# Setup logging (optional, can be removed)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# State tracking
states = {"option1": True, "suboption1": False, "suboption2": False}

# Custom style for colors
style = Style.from_dict(
    {
        "prompt": "#ffffff bold",
        "active": "#00ff00",  # Green
        "inactive": "#ff0000",  # Red
    }
)

# Key bindings
bindings = KeyBindings()


@bindings.add("q")
def exit_app(event):
    event.app.exit(result="q")
    logging.info("Exiting via key binding (q).")


@bindings.add("b")
def back_to_menu(event):
    event.app.exit(result="b")
    logging.info("Going back via key binding (b).")


@bindings.add("h")
def show_help(event):
    event.app.exit(result="h")
    logging.info("Showing help via key binding (h).")


for i in range(1, 10):  # Bind '1' to '9'

    @bindings.add(str(i))
    def _(event, number=str(i)):
        event.app.exit(result=number)
        logging.info(f"Selected option via key binding ({number}).")


# Menu classes
class MainMenu:
    def get_prompt(self, states):
        return HTML(
            "Main Menu:\n"
            f"[1] Submenu 1 <active>[{'Active' if states['option1'] else 'Inactive'}]</active>\n"
            "[2] Immediate Action\n"
            "Press [q] to quit, [h] for help\n> "
        )

    def get_completer(self):
        return WordCompleter(["1", "2", "q", "h"])

    def handle_choice(self, choice, states):
        if choice == "1":
            return "submenu1"  # Navigate to submenu1
        elif choice == "2":
            print("Executing immediate action...")
            states["option1"] = not states["option1"]
            return None  # Stay in current menu
        elif choice == "q":
            print("Exiting...")
            return "exit"
        elif choice == "h":
            return "help"
        else:
            print("Invalid choice.")
            return None


class Submenu1:
    def get_prompt(self, states):
        return HTML(
            "Submenu 1:\n"
            f"[1] Suboption 1 <inactive>[{'Active' if states['suboption1'] else 'Inactive'}]</inactive>\n"
            "[2] Submenu 2\n"
            "Press [b] to go back, [q] to quit, [h] for help\n> "
        )

    def get_completer(self):
        return WordCompleter(["1", "2", "b", "q", "h"])

    def handle_choice(self, choice, states):
        if choice == "1":
            print("Toggling suboption 1 state...")
            states["suboption1"] = not states["suboption1"]
            return None
        elif choice == "2":
            return "submenu2"
        elif choice == "b":
            return "back"
        elif choice == "q":
            print("Exiting...")
            return "exit"
        elif choice == "h":
            return "help"
        else:
            print("Invalid choice.")
            return None


class Submenu2:
    def get_prompt(self, states):
        return HTML(
            "Submenu 2:\n"
            f"[1] Suboption 2 <inactive>[{'Active' if states['suboption2'] else 'Inactive'}]</inactive>\n"
            "[2] Back\n"
            "Press [b] to go back, [q] to quit, [h] for help\n> "
        )

    def get_completer(self):
        return WordCompleter(["1", "2", "b", "q", "h"])

    def handle_choice(self, choice, states):
        if choice == "1":
            print("Toggling suboption 2 state...")
            states["suboption2"] = not states["suboption2"]
            return None
        elif choice in ("2", "b"):
            return "back"
        elif choice == "q":
            print("Exiting...")
            return "exit"
        elif choice == "h":
            return "help"
        else:
            print("Invalid choice.")
            return None


class HelpMenu:
    def get_prompt(self, states):
        return HTML(
            "Help:\n"
            "<active>[q]</active> - Quit the application\n"
            "<active>[h]</active> - Show this help\n"
            "<active>[b]</active> - Go back to parent menu (in submenus)\n"
            "<active>[1-9]</active> - Select numbered menu option\n"
            "Press any key to continue..."
        )

    def get_completer(self):
        return WordCompleter([])

    def handle_choice(self, choice, states):
        return "back"  # Always return to previous menu


# Menu registry
menu_registry = {
    "main": {"instance": MainMenu(), "parent": None},
    "submenu1": {"instance": Submenu1(), "parent": "main"},
    "submenu2": {"instance": Submenu2(), "parent": "submenu1"},
    "help": {"instance": HelpMenu(), "parent": None},
}


def run_cli():
    current_menu = "main"
    menu_stack = []
    session = PromptSession(multiline=False, style=style, key_bindings=bindings)

    while current_menu:
        menu = menu_registry[current_menu]
        try:
            choice = session.prompt(menu["instance"].get_prompt(states), completer=menu["instance"].get_completer())
            logging.info(f"Choice in {current_menu}: {choice}")
            result = menu["instance"].handle_choice(choice, states)

            if result == "exit":
                break
            elif result == "back" and menu["parent"] is not None:
                current_menu = menu_stack.pop() if menu_stack else menu["parent"]
            elif result == "help":
                menu_stack.append(current_menu)
                current_menu = "help"
            elif result in menu_registry:
                menu_stack.append(current_menu)
                current_menu = result
            else:
                continue  # Stay in current menu
        except KeyboardInterrupt:
            print("Exiting via Ctrl+C...")
            break
        except EOFError:
            print("Exiting via Ctrl+D...")
            break


if __name__ == "__main__":
    run_cli()
