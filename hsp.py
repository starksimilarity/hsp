import asyncio
import pickle
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings

from time import sleep

from utils.utils import parseconfig

from command import Command
from playback import Playback, merge_history

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"


bindings = KeyBindings()



async def main():
    files = parseconfig("histfile_list")

    hist = []

    playback_list = []
    for fi, hint in files.items():
        playback_list.append(Playback(fi, hint))

    playback = merge_history(playback_list)

    def toolbar():
        return HTML(
            f"PLAYBACK TIME: {playback.current_time}     "
            f"PLAYBACK MODE: {playback.playback_mode}    "
            f"PAUSED: {playback.paused}      "
            f"PLAYBACK RATE: {playback.playback_rate}"
        )

    @bindings.add('n')
    def _(event):
        async with playback.loop_lock:
            sleep(1)
            print("ahsdfieif")
   
    @bindings.add('p')
    def _(event):
        if playback.paused:
            playback.play()
        else:
            playback.pause()

    @bindings.add('f')
    def _(event):
        playback.speedup()

    @bindings.add('s')
    def _(event):
        playback.slowdown()

    #replace this with an application
    ps = PromptSession(bottom_toolbar=toolbar, key_bindings=bindings)

    # async loop:
    # configure playback to yield a Command after a certain time (depending on mode)
    # "run" the playback
    # await the function that yields the commands


    # set a key handler to release the loop_lock and immediately acquire it
    playback.playback_mode = "REALTIME"
     
    async for command in playback:
        print(command)


if __name__ == "__main__":
    # change this to asyncio.run(main()) if 3.7+ is required
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
