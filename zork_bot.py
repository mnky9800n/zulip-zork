import os
import re
import zulip
import pexpect
import sys

games = {
    "abyss": "abyss-r1-s890320.z6",
    "amfv": "amfv-r77-s850814.z4",
    "arthur": "arthur-r74-s890714.z6",
    "ballyhoo": "ballyhoo-r97-s851218.z3",
    "beyondzork": "beyondzork-r57-s871221.z5",
    "borderzone": "borderzone-r9-s871008.z5",
    "bureaucracy": "bureaucracy-r116-s870602.z4",
    "cutthroats": "cutthroats-r23-s840809.z3",
    "deadline": "deadline-r27-s831005.z3",
    "enchanter": "enchanter-r29-s860820.z3",
    "hitchhiker": "hitchhiker-r60-s861002.z3",
    "hollywoodhijinx": "hollywoodhijinx-r37-s861215.z3",
    "infidel": "infidel-r22-s830916.z3",
    "journey": "journey-r83-s890706.z6",
    "leathergoddesses": "leathergoddesses-r59-s860730.z3",
    "lurkinghorror": "lurkinghorror-r203-s870506.z3",
    "minizork2": "minizork2-r2-s871123.z3",
    "minizork": "minizork-r34-s871124.z3",
    "moonmist": "moonmist-r9-s861022.z3",
    "nordandbert": "nordandbert-r19-s870722.z4",
    "planetfall": "planetfall-r37-s851003.z3",
    "plunderedhearts": "plunderedhearts-r26-s870730.z3",
    "restaurant": "restaurant-r184-s890412.z6",
    "seastalker": "seastalker-r18-s850919.z3",
    "sherlock-nosound": "sherlock-nosound-r21-s871214.z5",
    "sherlock-nosound": "sherlock-nosound-r4-s880324.z5",
    "sherlock": "sherlock-r26-s880127.z5",
    "shogun": "shogun-r322-s890706.z6",
    "sorcerer": "sorcerer-r15-s851108.z3",
    "spellbreaker": "spellbreaker-r87-s860904.z3",
    "starcross": "starcross-r17-s821021.z3",
    "stationfall": "stationfall-r107-s870430.z3",
    "suspect": "suspect-i190-r18-s850222.z3",
    "suspended": "suspended-mac-r8-s840521.z3",
    "trinity": "trinity-r12-s860926.z4",
    "wishbringer": "wishbringer-r69-s850920.z3",
    "witness": "witness-r22-s840924.z3",
    "zork0": "zork0-r393-s890714.z6",
    "zork1": "zork1-r88-s840726.z3",
    "zork2": "zork2-r48-s840904.z3",
    "zork3": "zork3-r17-s840727.z3",
}

GAME_CHANNEL = os.environ.get("ZORK_CHANNEL", "play-zork")
GAME_TOPIC = os.environ.get("ZORK_TOPIC", "adventure")
GAME_NAME = os.environ.get("GAME_NAME")
GAME_NAME = games[GAME_NAME]
GAME_PREFIX = "/game"
SAVE_DIR = "/save"
# GAME_DAT = os.environ.get("ZORK_DAT", "/home/frotz/DATA/ZORK1.DAT")
GAME_DAT = os.environ.get("ZORK_DAT", f"/home/frotz/DATA/{GAME_NAME}")


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
        if msg.get("display_recipient") != self.channel and msg["subject"] != self.topic:
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
