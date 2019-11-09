import datetime


class Command:
    """Defines the structure of a single command

    Attributes
    ==========
    time : datetime.datetime
        time that the command was run
    user : str
        user who ran the command
    hostUUID : str
        ID of the the host
    command : str
        the command the user issued
    result : str
        the result from the command
    flagged : bool
        event is marked
    comments : str
        comments for replay

    Methods
    =======
    to_dict(self)
        Returns a dictionary representation of the command
    __str__(self)
        how to display the command when printed
    """

    def __init__(
        self,
        time,
        user=None,
        hostUUID=None,
        command=None,
        result=None,
        flagged=False,
        comment="",
        *args,
        **kwargs,
    ):
        self.time = time
        self.user = user
        self.hostUUID = hostUUID
        self.command = command
        self.result = result
        self.flagged = flagged
        self.comment = comment

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
        """time that the command was run
        """
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
        """user who ran the command
        """
        return self._user

    @user.setter
    def user(self, val):
        self._user = val

    @property
    def hostUUID(self):
        """ID of the the host
        """
        return self._hostUUID

    @hostUUID.setter
    def hostUUID(self, val):
        self._hostUUID = val

    @property
    def command(self):
        """the command the user issued
        """
        return self._command

    @command.setter
    def command(self, val):
        self._command = val

    @property
    def result(self):
        """the result from the command
        """
        return self._result

    @result.setter
    def result(self, val):
        self._result = val

    @property
    def flagged(self):
        return self._flagged

    @flagged.setter
    def flagged(self, val):
        if isinstance(val, bool):
            self._flagged = val
        else:
            raise TypeError("flagged attribute must be of type bool")

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, val):
        self._comment = val

