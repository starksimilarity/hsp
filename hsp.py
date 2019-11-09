import asyncio
import pickle
from time import sleep

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Box, Frame, TextArea

from prompt_toolkit.eventloop import use_asyncio_event_loop


from command import Command
from playback import Playback, merge_history
from utils.utils import parseconfig

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"


bindings = KeyBindings()


def main():
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

    @bindings.add("n")
    def _(event):
        try:
            playback.loop_lock.release()
        except Exception as e:
            pass

    @bindings.add("p")
    def _(event):
        if playback.paused:
            playback.play()
        else:
            playback.pause()

    @bindings.add("f")
    def _(event):
        playback.speedup()

    @bindings.add("s")
    def _(event):
        playback.slowdown()

    @bindings.add("q")
    def _(event):
        event.app.exit()

    @bindings.add("c-c")
    def _(event):
        event.app.exit()

    playback.playback_mode = "MANUAL"

    # a = Application(layout=Layout(container=body), full_screen=True, key_bindings=bindings)
    a = Application(full_screen=True, key_bindings=bindings)

    # async loop:
    # configure playback to yield a Command after a certain time (depending on mode)
    # "run" the playback
    # await the function that yields the commands
    async def command_loop():
        async for command in playback:
            if playback.playback_mode == "MANUAL":
                print("herehere")
                await playback.loop_lock.acquire()
            print(command)
        else:
            print("\n\n\nDONEDONEDONE\n\n\n")

    loop = asyncio.get_event_loop()
    use_asyncio_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(command_loop(), a.run_async().to_asyncio_future())
        )
    finally:
        loop.close()



if __name__ == "__main__":
    main()
