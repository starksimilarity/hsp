import pickle
from prompt_toolkit import PromptSession, HTML
from utils.utils import parseconfig

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"

from command import Command


class Playback:
    def __init__(self, histfile=None, histfile_typehint=None, playback_mode=None):
        self.current_time = 0
        self.playback_mode = playback_mode

        if histfile:
            self._hist = self.load_hist(histfile, histfile_typehint)
        else:
            self._hist = []

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
            print("loading pickle info...")
            commands = pickle.load(open(f"sessions/{histfile}", "rb"))
            hist = [x for x in commands if isinstance(x, Command)]
            return hist
        if histfile_typehint == "msf_prompt":
            print("loading msf_prompt info...")
            return [Command(1, "stark", 2010, "ls", "asdf")]

    @property
    def hist(self):
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
        # can't directly extend the history because of some property masking
        extended = combined_playback.hist + pb.hist
        combined_playback.hist = extended
    print(combined_playback.hist)
    return combined_playback
