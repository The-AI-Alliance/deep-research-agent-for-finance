# Common utilities for handling user input and output.

from rich.console import Console
from rich.prompt  import Confirm, Prompt

class UserPrompts():
    """
    Prompt the user for information.
    See https://rich.readthedocs.io/en/stable/prompt.html for other prompt
    features that could be implemented (TODO).
    """
    def __init__(self):
        self.console = Console(highlight=False, soft_wrap=False, emoji=False)

    def read_multi_line_input(self, 
        prompt: str, 
        default: str = None,
        empty_allowed: bool = False) -> str:
        """
        Allow the user to provide multi-line input, either typed or using copy and paste.
        """     
        while True:
            p = f"[blue]{prompt}. Multiple lines are fine. Use ^D or the word 'done' on its own line when finished:[/blue]"
            self.console.print(p)

            # Source - https://stackoverflow.com/a/36237166
            # Posted by arekolek, modified by community. See post 'Timeline' for change history
            # Retrieved 2026-02-17, License - CC BY-SA 4.0

            lines = []
            try:
                while True:
                    line = Prompt.ask("", default=default)
                    if not line == None:
                        l = line.strip()
                        if l == "done":
                            break;
                        lines.append(line)
            except (KeyboardInterrupt, EOFError):
                pass
            self.console.print("")
            answer = "\n".join(lines)
            if answer or empty_allowed:
                return answer

    def read_one_line_input(self, 
        prompt: str, 
        choices: list[str] = None,
        default: str = None,
        empty_allowed: bool = False) -> str:
        """
        Prompt the user for a single line of text input.
        """     
        while True:
            answer = Prompt.ask(f"[green]{prompt}[/green]",
                choices=choices, default=default).strip()
            if answer or empty_allowed:
                return answer

    def confirm(self, prompt) -> str:
        """
        Prompt the user for yes/no answer.
        """     
        return Confirm.ask(prompt)