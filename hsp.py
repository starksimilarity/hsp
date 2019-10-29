import pickle
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar
from prompt_toolkit.formatted_text import HTML

from utils.utils import parseconfig

from command import Command
from playback import Playback, merge_history

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"


def main():
    files = parseconfig("histfile_list")

    hist = []

    playback_list = []
    for fi, hint in files.items():
        playback_list.append(Playback(fi, hint))

    playback = merge_history(playback_list)
    # toolbar = FormattedTextToolbar(HTML('toolbar test'))

    def toolbar():
        return HTML(f"PLAYBACK TIME: {playback.current_time}     "
                    f"PLAYBACK MODE: {playback.playback_mode}")
    ps = PromptSession(bottom_toolbar=toolbar)

    for command in playback:
        ps.prompt("enter for next")
        print(command)

if __name__ == "__main__":
    main()
