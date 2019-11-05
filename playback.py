import asyncio
import datetime
import pickle
from time import sleep
from utils.utils import parseconfig

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"

from command import Command
from loader import PBLoader, OffPromptPBLoader, PicklePBLoader


class Playback:
    """Main class that keeps track of history, current_time, and modes during a playback.

    Attributes
    ==========
    current_time : datetime.datetime
        The time that the playback session is set to
    playback_mode : int
        The type of playback for the session (e.g. real-time, manual, eveninterval)
    hist : list[Command]
        List of Commands to replay during the Playback

    Methods
    =======
    load_hist(histfile, histfile_typehint)
        set the Playback's history


    """

    modes = ["MANUAL", "REALTIME", "EVENINTERVAL",]

    def __init__(
        self,
        histfile=None,
        histfile_typehint=None,
        user_hint=None,
        host_hint=None,
        date_hint=None,
        playback_mode=None,
    ):
        self.current_time = 0
        self.playback_position = 0
        self.playback_interval = 10
        self.user_hint = user_hint
        self.host_hint = host_hint
        self.date_hint = date_hint
        self.playback_mode = playback_mode
        self.loop_lock = asyncio.Lock()
        self.paused = False
        self.playback_rate = 5
        self._start_time =  datetime.datetime.now() # when the replay was unpaused; 
        self._elapsed_time_at_pause = datetime.timedelta(0) 

        if histfile:
            self.hist = self.load_hist(histfile, histfile_typehint)
        else:
            self.hist = []

    def __iter__(self):
        return self

    def __next__(self):
        try:
            # set current playback time to time of the command
            self.current_time = self.hist[self.playback_position].time
            self.playback_position += 1
            return self.hist[self.playback_position]
        except IndexError as e:
            raise StopIteration(e)


    async def __aiter__(self):
        # set start-time for REALTIME mode
        self._start_time = datetime.datetime.now()
        self.play()
        return self

    async def __anext__(self):
        try:
            # These if statements control when the function should 
            if self.playback_mode == "MANUAL":
                #not implemented
                print(self.loop_lock)
                async with self.loop_lock:
                    pass
                sleep(1) # remove after debugging
            elif self.playback_mode == "REALTIME":
                # check to see if the diff between now and the "start time" is
                # less than the diff between the playback_position and first 
                # command time
                #
                # BUG: this does not allow for pausing
                while (((datetime.datetime.now() - self._start_time) + \
                        self._elapsed_time_at_pause) * self.playback_rate) < \
                        (
                            self.hist[self.playback_position].time - 
                            self.hist[0].time
                        ):
                    asyncio.sleep(1)

            elif self.playback_mode == "EVENINTERVAL":
                # yield for pre-determined amount of time
                asyncio.sleep(self.playback_interval)

            self.current_time = self.hist[self.playback_position].time
            self.playback_position += 1
            return self.hist[self.playback_position-1]
        except IndexError as e:
            raise StopIteration(e)

    def load_hist(self, histfile, histfile_typehint=None):
        """Sets the playback's history.

        Parameters
        ==========
        histfile : str
            location of the history file to load
        histfile_typehint : str
            string of the history file type to help aid in parsing

        Returns
        =======
        hist : list[Commands]
            Ordered list of Commands
        """
        hints = {
            'user_hint':self.user_hint,
            'host_hint':self.host_hint,
            'date_hint':self.date_hint,
        }

        if histfile_typehint == "pickle":
            return PicklePBLoader.load(histfile, *hints)
        if histfile_typehint == "msf_prompt":
            return OffPromptPBLoader.load(histfile, *hints)

    @property
    def hist(self):
        """the command history for the playback sorted by time
        """
        return sorted(self._hist, key=lambda x: x.time)

    @hist.setter
    def hist(self, val):
        self._hist = val

    @property
    def playback_mode(self):
        return self._playback_mode

    @playback_mode.setter
    def playback_mode(self, val):
        if val in self.modes:
            self._playback_mode = val
        else:
            self._playback_mode = "MANUAL"

    @property
    def playback_interval(self):
        return self._playback_interval

    @playback_interval.setter
    def playback_interval(self, val):
        if isinstance(val, int) and val > 0:
            self._playback_interval = val

        else:
            raise TypeError("Must be of type int and greater than 0")

    @property
    def playback_rate(self):
        return self._playback_rate

    @playback_rate.setter
    def playback_rate(self, val):
        self._playback_rate = val

    @property
    def paused(self):
        return self._paused

    @paused.setter
    def paused(self, val):
        if isinstance(val, bool):
            self._paused = val
        else:
            raise TypeError("Paused state must be of type bool")

    def pause(self):
        self._elapsed_time_at_pause += (datetime.datetime.now() - self._start_time)
        print(f"elapsed_time = {self._elapsed_time_at_pause}")
        self.paused = True

    def play(self):
        self._start_time = datetime.datetime.now()
        print(f"start_time = {self._start_time}")
        self.paused = False


def merge_history(playbacks):
    """Returns a single, consolidated Playback from a list of multiple playbacks

    #future: If all playback modes match, the playback mode will remain the same. Otherwise it will
    revert to manual.

    Parameters
    ==========
    playbacks : list[playback.Playback]
        list of playbacks from multiple sessions

    Returns
    =======
    combined_playback : playback.Playback
        a single Playback that merges all events of input Playbacks
    """
    combined_playback = Playback()
    for pb in playbacks:
        try:
            # can't directly extend the history because of some property masking
            extended = combined_playback.hist + pb.hist
            combined_playback.hist = extended
        except Exception as e:
            print(e)
            continue
    return combined_playback
