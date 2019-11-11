"""Example UI for creating and controlling a playback object

Creates a playback object and a prompt_toolkit Application and runs
each asynchronously.

Author: starksimilarity@gmail.com
"""

import asyncio

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.key_binding import KeyBindings

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout import Layout, Dimension
from prompt_toolkit.widgets import Box, Frame, TextArea

from prompt_toolkit.eventloop import use_asyncio_event_loop


from playback import Playback, merge_history
from utils.utils import parseconfig

DEFAULT_HIST = "sessions/histfile"
HISTFILE_LIST = "histfile_list"


def main():
    """Sets up playback and app then runs both in async loop
    """
    files = parseconfig("histfile_list")

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

    @bindings.add("c-m")
    def _(event):
        playback.change_playback_mode()

    @bindings.add("c")
    def _(event):
        # future: add comment
        pass

    @bindings.add("f")
    def _(event):
        # future: flag command
        pass

    def toolbar():
        """Returns bottom toolbar for app

        Returns
        =======
        _ : prompt_toolkit.formatted_text.HTML
            Text for the bottom toolbar for the app
        """
        return HTML(
            "<table><tr>"
            f"<th>PLAYBACK TIME: {playback.current_time}</th>     "
            f"<th>PLAYBACK MODE: {playback.playback_mode}</th>    "
            f"<th>PAUSED: {playback.paused}</th>      "
            f"<th>PLAYBACK RATE: {playback.playback_rate}</th>"
            "</tr></table>"
        )

    old_command_window = FormattedTextControl(text="Output goes here", focusable=True)
    new_command_window = FormattedTextControl(text="Output goes here", focusable=True)

    body = Frame(
        HSplit([Frame(Window(old_command_window)), Frame(Window(new_command_window))])
    )

    root_container = HSplit(
        [
            body,
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
        """Return string of command object specific to this UI

        Parameters
        ==========
        command : command.Command
            Command object to get string for

        Returns
        =======
        _ : str
            String representation of Command object
        """
        try:
            if command.flagged:
                color = "ansired"
            else:
                color = "ansiwhite"
        except:
            color = "ansiwhite"
        try:
            return [
                ("bg:ansiblue ansiwhite", f"{command.time.ctime()}\n"),
                (
                    color,
                    (
                        f"{command.hostUUID}:{command.user} > {command.command}\n"
                        f"{command.result}"
                    ),
                ),
            ]
        except:
            # if this happens, we probaly didn't get an actual Command object
            # but we can have it rendered in the window anyway
            return [(color, str(command))]

    def display_new_command(command):
        """Moves text from lower window to upper then adds new command text
        """
        a.layout.focus(old_command_window)
        a.layout.current_control.text = new_command_window.text
        a.layout.focus(new_command_window)
        a.layout.current_control.text = FormattedText(render_command(command))
        a.invalidate()

    async def command_loop():
        """Primary loop for receiving/displaying commands from playback

        Asynchronously iterates over the Command objects in the playback's history.
        Takes the command object and displays it to the screen
        """
        # give this thread control over playback for manual mode
        # lock is released by certain key bindings
        await playback.loop_lock.acquire()
        async for command in playback:
            if playback.playback_mode == "MANUAL":
                # regain the lock for MANUAL mode
                await playback.loop_lock.acquire()

            # Update text in windows
            display_new_command(command)
        else:
            display_new_command("\n\n\nDONEDONEDONEDONE\n\n\n")

    loop = asyncio.get_event_loop()
    use_asyncio_event_loop()
    try:
        # Run command_loop and a.run_async next to each other
        # future: handle when one completes before the other
        loop.run_until_complete(
            asyncio.gather(command_loop(), a.run_async().to_asyncio_future())
        )
    finally:
        loop.close()


if __name__ == "__main__":
    main()
