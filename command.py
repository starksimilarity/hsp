import pickle
import datetime


class Command:
    def __init__(self, time=None, user=None, hostUUID=None, command=None, result=None):
        self.time = time
        self.user = user
        self.hostUUID = hostUUID
        self.command = command
        self.result = result

    def __str__(self):
        return (
            f"==========================\n{self.time}\n"
            f"{self.hostUUID}:{self.user} >>> {self.command}\n{self.result}"
        )

    def to_dict(self):
        """Return a dictionary representation of the command
        """
        return {self.time: (self.user, self.hostUUID, self.command, self.result)}

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, val):
        if isinstance(val, datetime.datetime):
            self._time = val
        elif isinstance(val, int):
            self._time = datetime.datetime.fromordinal(val)
        else:
            raise TypeError("Time must be of datetime or int type")

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, val):
        self._user = val

    @property
    def hostUUID(self):
        return self._hostUUID

    @hostUUID.setter
    def hostUUID(self, val):
        self._hostUUID = val

    @property
    def command(self):
        return self._command

    @command.setter
    def command(self, val):
        self._command = val

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, val):
        self._result = val
