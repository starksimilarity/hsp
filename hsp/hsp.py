"""Example UI for creating and controlling a playback object

Creates a playback object and a prompt_toolkit Application and runs
each asynchronously.

Author: starksimilarity@gmail.com
"""

import asyncio
from prompt_toolkit.eventloop import use_asyncio_event_loop

from playback import Playback, merge_history
from utils.utils import parseconfig
from hspApp import HspApp

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
    # Setting Up HspApp object
    ###################################################
    hspApp = HspApp(playback, SAVE_LOCATION)

    ###################################################
    # Setting Up async loop
    ###################################################
    loop = asyncio.get_event_loop()
    use_asyncio_event_loop()
    try:
        # Run msg_consumer and hspApp.run_async next to each other
        # future: handle when one completes before the other
        loop.run_until_complete(
            asyncio.gather(
                hspApp.run_async().to_asyncio_future(),
                hspApp.msg_consumer(loop),
                hspApp.playback.run_async(),
                # hspApp.redraw_timer(),
            )
        )
    finally:
        loop.close()


if __name__ == "__main__":
    main()
