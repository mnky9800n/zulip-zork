import yaml

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

services = {}
for name in games:
    services[f"{name}-bot"] = {
        "build": ".",
        "volumes": [
            "./saves:/save",
            "./zuliprc:/app/zuliprc:ro",
        ],
        "environment": [
            f"ZORK_CHANNEL=${{ZORK_CHANNEL:-play-zork}}",
            f"ZORK_TOPIC=${{ZORK_TOPIC:-{name}}}",
            f"GAME_NAME={name}",
        ],
        "restart": "unless-stopped",
    }

compose = {"services": services}

with open("docker-compose.yml", "w") as f:
    yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

print(f"Generated docker-compose.yml with {len(services)} services")
