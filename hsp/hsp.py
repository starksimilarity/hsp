"""Example UI for creating and controlling a playback object

Creates a playback object and a prompt_toolkit Application and runs
each asynchronously.

Author: starksimilarity@gmail.com
"""

import asyncio
from prompt_toolkit.eventloop import use_asyncio_event_loop

from hspApp import HspApp

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"
SAVE_LOCATION = "SavedPlayback"


def main():
    """Sets up hspApp then runs in async loop
    """

    ###################################################
    # Setting Up HspApp object
    ###################################################
    hspApp = HspApp(SAVE_LOCATION)

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
                hspApp.msg_consumer(),
                # hspApp.redraw_timer(), # not convinced this does anything meaningful
            )
        )
    finally:
        loop.close()


if __name__ == "__main__":
    main()
