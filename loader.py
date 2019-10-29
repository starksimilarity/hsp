from abc import ABC, abstractmethod
import datetime as dt
import pickle
import re

from command import Command


class PBLoader(ABC):
    @classmethod
    @abstractmethod
    def load(cls):
        return False


class PicklePBLoader(PBLoader):
    @classmethod
    def load(cls, filename):
        commands = pickle.load(open(f"sessions/{filename}", "rb"))
        hist = [x for x in commands if isinstance(x, Command)]
        return hist


class OffPromptPBLoader(PBLoader):
    @classmethod
    def load(cls, filename):
        commandhist = []
        rawhist = ""
        with open(f"sessions/{filename}", "r+") as infi:
            rawhist = infi.read()

        commands = re.findall(
            "=\n([0-9\-\W:,]+)\n"  # datetime
            "\[COMMAND\]\[USER: (.*?)\]\n"  # user
            "(.*?)={4,}.*?\[RESULT\]"  # command
            "(.*?)={8,}\n",
            rawhist,
            re.DOTALL,
        )  # result
        for c in commands:
            try:
                # datetime.datetime.fromisoformat would solve this perfectly, but is introduced in python 3.7
                yr, mon, day, hr, mn, sec = re.findall(
                    "([0-9]{4})-"  # yr
                    "([0-9]{2})-"  # mon
                    "([0-9]{2}) "  # day
                    "([0-9]{2}):"  # hr
                    "([0-9]{2}):"  # mn
                    "([0-9]{2})",
                    c[0],
                )[
                    0
                ]  # only expecting one result so grab the first and unpack

                # this portion isn't strictly necessary but it makes the
                # build of Command so much cleaner
                time = dt.datetime(
                    int(yr), int(mon), int(day), int(hr), int(mn), int(sec)
                )
                user = c[1]
                user_command = c[2].strip("+").strip()
                if user_command == "exit":
                    # this prevents the new session from being the "result" of exit
                    result = ""
                else:
                    result = c[3]
                commandhist.append(Command(time, user, "unknown", user_command, result))
            except Exception as e:
                print(e)

        return commandhist
