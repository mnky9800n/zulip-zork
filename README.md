```
 ______  ___  ____  _  __
|__  / / _ \|  _ \| |/ /
  / / | | | | |_) | ' /
 / /_ | |_| |  _ <| . \
/____| \___/|_| \_\_|\_\
```

# zulip-zork

A Zulip bot that lets your team play Zork I together in a channel.

Commands go through `/game` — everything else is just chat.

```
/game look        # look around
/game go north    # move
/game take lamp   # pick up items
/game save        # save the game
/game restore     # load a save
/game restart     # start over
```

## Setup

1. Create a bot in Zulip (Settings > Bots) and download the `zuliprc` file
2. Place `zuliprc` in the project root
3. Create a channel (default: `#play-zork`)
4. `docker compose up --build -d`

## Comments

`zulip-zork` is based on [Bot-Builder](https://github.com/TansyArron/Bot-Builder) and [docker-zork1](https://github.com/TansyArron/Bot-Builder).
