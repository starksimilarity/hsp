import pickle
from prompt_toolkit import PromptSession, HTML
from utils.utils import parseconfig

from command import Command
from playback import Playback, merge_history

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"


def main():
    files = parseconfig("histfile_list")
    print(files)

    hist = []

    playback_list = []
    for fi, hint in files.items():
        playback_list.append(Playback(fi, hint))

    playback = merge_history(playback_list)
    ps = PromptSession()

    for command in playback.hist:
        ps.prompt("enter for next")
        print(command)


if __name__ == "__main__":
    main()
