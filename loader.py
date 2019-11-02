from abc import ABC, abstractmethod
import datetime as dt
import pickle
import re

from command import Command


class PBLoader(ABC):
    """Class that defines one abstract classmethod for loading a history

    Subclasses can be developed to load a particular type of file history,
    for example loading a file produced by the unix "script" command
    
    AbstractMethods
    ===============
    @classmethod
    @abstractmethod
    load(cls, filename) -> list[command.Command]
        load a history from a filename
    """

    @classmethod
    @abstractmethod
    def load(cls, filename, user_hint=None, host_hint=None, date_hint=None):
        """Load a history from a filename

        Parameters
        ==========
        filename : str
            filename of the history file
        user_hint : str
            hint of what the user should be if not found in the history
        host_hint : str
            hint of what the hostUUID should be if not found in the history
        date_hint : str
            hint of what the date should be if not found in the history


        Returns
        =======
        list[command.Command]
            List of Command objects from the history
        """
        return []


class PicklePBLoader(PBLoader):
    """Class for loading pickled lists of commands.
    """

    @classmethod
    def load(cls, filename, user_hint=None, host_hint=None, date_hint=None):
        """Load history for pickled list of Commands

        This loader assumes that the pickle being loaded is already
        a list of Command objects.  It creates a new list to verify that
        what was loaded is in fact a list of Command objects and will drop
        anything that is not.

        Returns
        =======
        list[command.Command]
            List of Command objects from pickle file
        """

        commands = pickle.load(open(f"sessions/{filename}", "rb"))
        hist = [x for x in commands if isinstance(x, Command)]
        return hist


class OffPromptPBLoader(PBLoader):
    """Class for loading histories generated by an msf_prompt.OffPromptSession 
    """

    @classmethod
    def load(cls, filename, user_hint=None, host_hint=None, date_hint=None):
        """Load log from msf_prompt.OffPromptSession

        For an OffPromptSession, a history only includes the command and timestamp,
        but the log file contains time, user, command, and result.  
        The format of an OffPromptSession log is :
            =================
            <time>
            [COMMAND][USER: <user>]
            <command>

            ...
            =================
            <time>
            [RESULT]
            <result>
        """
        commandhist = []
        rawhist = ""
        with open(f"sessions/{filename}", "r+") as infi:
            rawhist = infi.read()

        # future : consider making this more performant
        commands = re.findall(
            "=\n([0-9\-\W:,]+)\n"  # datetime
            "\[COMMAND\]\[USER: (.*?)\]\n"  # user
            "(.*?)={4,}.*?\[RESULT\]"  # command
            "(.*?)={8,}\n",  # result
            rawhist,
            re.DOTALL,
        )

        for c in commands:
            try:
                # datetime.datetime.fromisoformat would solve this perfectly,
                # but is not introduced until python 3.7
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
