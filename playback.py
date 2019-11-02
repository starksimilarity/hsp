import pickle
from prompt_toolkit import PromptSession, HTML
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
        The type of playback for the session (e.g. real-time, paused, 5x, Nx)
    hist : list[Command]
        List of Commands to replay during the Playback

    Methods
    =======
    load_hist(histfile, histfile_typehint)
        set the Playback's history


    """

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
        self.user_hint = user_hint
        self.host_hint = host_hint
        self.date_hint = date_hint
        self.playback_mode = playback_mode

        if histfile:
            self.hist = self.load_hist(histfile, histfile_typehint)
        else:
            self.hist = []

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

        if histfile_typehint == "pickle":
            return PicklePBLoader.load(histfile)
        if histfile_typehint == "msf_prompt":
            return OffPromptPBLoader.load(histfile)

    @property
    def hist(self):
        """the command history for the playback sorted by time
        """
        return sorted(self._hist, key=lambda x: x.time)

    @hist.setter
    def hist(self, val):
        self._hist = val


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
    print(combined_playback.hist)
    return combined_playback
