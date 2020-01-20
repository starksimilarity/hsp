"""Creates a playback object and runs it asynchronously

Author: starksimilarity@gmail.com
"""

import asyncio

from playback import Playback, merge_history
from utils.utils import parseconfig

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"
SAVE_LOCATION = "SavedPlayback"


def main():
    """Sets up playback and app then runs both in async loop
    """

    ###################################################
    # Setting Up Playback object
    ###################################################

    files = parseconfig("histfile_list")

    playback_list = []
    for fi, hint in files.items():
        playback_list.append(Playback(fi, hint))

    playback = merge_history(playback_list)
    playback.playback_mode = "MANUAL"

    ###################################################
    # Setting Up async loop
    ###################################################
    loop = asyncio.get_event_loop()
    try:
        # Run msg_consumer and hspApp.run_async next to each other
        # future: handle when one completes before the other
        loop.run_until_complete(
            asyncio.gather(
                playback.run_async(),
                playback.run_timers(),
                playback.cmd_consumer(loop),
            )
        )
    finally:
        loop.close()


if __name__ == "__main__":
    main()
