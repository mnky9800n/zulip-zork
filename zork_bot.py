import os
import re
import zulip
import pexpect
import sys

GAME_CHANNEL = os.environ.get("ZORK_CHANNEL", "play-zork")
GAME_TOPIC = os.environ.get("ZORK_TOPIC", "adventure")
GAME_PREFIX = "/game"
SAVE_DIR = "/save"
# GAME_DAT = os.environ.get("ZORK_DAT", "/home/frotz/DATA/ZORK1.DAT")
GAME_DAT = os.environ.get("ZORK_DAT", "/home/frotz/DATA/zork1-r88-s840726.z3")


class ZorkSession:
    """Manages a persistent frotz subprocess."""

    def __init__(self, game_dat: str, save_dir: str):
        self.game_dat = game_dat
        self.save_dir = save_dir
        self.process = None
        self.start()

    def start(self):
        self.process = pexpect.spawn(
            f"/usr/games/dfrotz {self.game_dat}",
            cwd=self.save_dir,
            encoding="utf-8",
            timeout=5,
            logfile=sys.stdout
        )
        # Read the initial game output
        self._read_until_prompt()

    def _read_until_prompt(self) -> str:
        """Read frotz output until it's waiting for input."""
        try:
            # frotz prompts end with ">" on a new line
            self.process.expect(r"\n>", timeout=5)
            output = self.process.before
            # Clean up frotz terminal escape codes
            output = re.sub(r"\x1b\[[^a-zA-Z]*[a-zA-Z]", "", output)
            return output.strip()
        except pexpect.TIMEOUT:
            # Grab whatever output is available
            output = self.process.before or ""
            output = re.sub(r"\x1b\[[^a-zA-Z]*[a-zA-Z]", "", output)
            return output.strip()
        except pexpect.EOF:
            return "[Game process ended. Restarting...]"

    def send_command(self, command: str) -> str:
        """Send a command to the Zork game and return the response."""
        if self.process is None or not self.process.isalive():
            self.start()
            return "[Game restarted]\n\n" + self.send_command(command)

        self.process.sendline(command)
        response = self._read_until_prompt()

        # The response usually includes the echoed command at the start; strip it
        lines = response.split("\n")
        if lines and command.lower() in lines[0].lower():
            response = "\n".join(lines[1:]).strip()

        return response if response else "[No response from game]"

    def restart(self):
        """Kill and restart the game process."""
        if self.process and self.process.isalive():
            self.process.terminate(force=True)
        print(self.process.exitstatus, '\n\n', self.process.signalstatus)
        self.start()


class ZorkBot:
    """Zulip bot that bridges chat to a Zork game."""

    def __init__(self):
        self.client = zulip.Client(config_file="zuliprc")
        self.zork = ZorkSession(GAME_DAT, SAVE_DIR)
        self.channel = GAME_CHANNEL
        self.topic = GAME_TOPIC

    def send(self, content: str, topic: str | None = None):
        self.client.send_message({
            "type": "stream",
            "to": self.channel,
            "topic": topic or self.topic,
            "content": content,
        })

    def handle_message(self, msg: dict):
        # Ignore our own messages
        if msg["sender_email"] == self.client.email:
            return

        # Only respond in our channel
        if msg.get("display_recipient") != self.channel:
            return

        content = msg["content"].strip()

        print(msg)

        # Check for /game prefix
        if not content.startswith(GAME_PREFIX):
            return

        command = content[len(GAME_PREFIX):].strip()

        if not command:
            self.send(
                "**Zork Bot Help**\n\n"
                "Send commands to Zork with `/game <command>`\n\n"
                "Examples:\n"
                "- `/game look` - Look around\n"
                "- `/game go north` - Move north\n"
                "- `/game take lamp` - Pick up the lamp\n"
                "- `/game save` - Save your game\n"
                "- `/game restore` - Restore a saved game\n"
                "- `/game inventory` - Check your inventory\n\n"
                "Special:\n"
                "- `/game restart` - Restart the game from scratch\n\n"
                "Any message without `/game` is just chat — discuss strategy with your friends!",
                topic=msg.get("subject", self.topic),
            )
            return

        # Handle restart specially
        if command.lower() == "restart":
            self.zork.restart()
            self.send(
                "**Game restarted!** Type `/game look` to begin.",
                topic=msg.get("subject", self.topic),
            )
            return

        # Send command to Zork
        sender = msg.get("sender_full_name", "Someone")
        response = self.zork.send_command(command)

        formatted = (
            f"**{sender}** > `{command}`\n\n"
            f"```\n{response}\n```"
        )
        self.send(formatted, topic=msg.get("subject", self.topic))

    def subscribe(self):
        result = self.client.add_subscriptions(
            streams=[{"name": self.channel}],
        )
        if result["result"] == "success":
            print(f"Subscribed to #{self.channel}")
        else:
            print(f"Failed to subscribe: {result}")

    def run(self):
        print(f"Zork bot starting on #{self.channel}...")
        self.subscribe()
        self.send("**Zork Bot is online!** Send `/game look` to start playing. "
                   "Messages without `/game` are just chat.")
        self.client.call_on_each_message(self.handle_message)


if __name__ == "__main__":
    bot = ZorkBot()
    bot.run()
