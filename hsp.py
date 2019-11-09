import asyncio
import pickle

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, Window, FloatContainer
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout import Layout, Dimension
from prompt_toolkit.widgets import Box, Frame, TextArea

from prompt_toolkit.eventloop import use_asyncio_event_loop


from command import Command
from playback import Playback, merge_history
from utils.utils import parseconfig

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"


def main():
    files = parseconfig("histfile_list")

    hist = []

    playback_list = []
    for fi, hint in files.items():
        playback_list.append(Playback(fi, hint))

    playback = merge_history(playback_list)

    bindings = KeyBindings()

    @bindings.add("n")
    @bindings.add("down")
    @bindings.add("right")
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
    @bindings.add("c-c")
    def _(event):
        event.app.exit()

    def toolbar():
        return HTML(
            "<table><tr>"
            f"<th>PLAYBACK TIME: {playback.current_time}</th>     "
            f"<th>PLAYBACK MODE: {playback.playback_mode}</th>    "
            f"<th>PAUSED: {playback.paused}</th>      "
            f"<th>PLAYBACK RATE: {playback.playback_rate}</th>"
            "</tr></table>"
        )

    main_area = FormattedTextControl(text="Output goes here", focusable=True)
    body = Frame(Window(main_area))

    root_container = HSplit(
        [
            body,
            # Window(height=1, char='-', style='class:line', dont_extend_height=True),
            Window(
                FormattedTextControl(text=toolbar),
                height=Dimension(max=1, weight=10000),
                dont_extend_height=True,
            ),
        ],
        padding_char="-",
    )
    a = Application(
        layout=Layout(root_container), full_screen=True, key_bindings=bindings
    )

    playback.playback_mode = "MANUAL"

    def render_command(command):
        return (
            f"{command.hostUUID}:{command.user} > {command.command}\n"
            f"{command.result}"
        )

    async def command_loop():
        await playback.loop_lock.acquire()  # give this thread control over playback for manual mode
        async for command in playback:
            if playback.playback_mode == "MANUAL":
                await playback.loop_lock.acquire()
            # print(command)
            # a.print_text(str(command))
            a.layout.focus(main_area)
            a.layout.current_control.text = render_command(command)
            a.invalidate()
        else:
            a.layout.focus(main_area)
            a.layout.current_control.text = "\n\n\nDONEDONEDONE\n\n\n"

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
