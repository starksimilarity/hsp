"""Example UI for creating and controlling a playback object

Creates a playback object and a prompt_toolkit Application and runs
each asynchronously.

Author: starksimilarity@gmail.com
"""

import asyncio
import datetime
import pickle

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.key_binding import KeyBindings

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout import Layout, Dimension
from prompt_toolkit.widgets import Box, Frame, TextArea
from prompt_toolkit.filters import Condition

from prompt_toolkit.eventloop import use_asyncio_event_loop


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
    # Setting Up prompt_toolkit Application view
    ###################################################

    # must define this up front because follow-on definitions depend on it
    # this gets updated with layouts and keybindings
    hspApp = Application(full_screen=True)
    hspApp.displayingHelpScreen = False  # used to toggle between help screen on normal
    hspApp.savedLayout = Layout(Window())

    bindings = KeyBindings()

    @Condition
    def mainView():
        """Return if app is in main view.

        Returns
        =======
        _ : bool
            If app is not displaying the Help Screen, it's in main view
        """
        return not hspApp.displayingHelpScreen

    @bindings.add("n", filter=mainView)
    @bindings.add("down", filter=mainView)
    @bindings.add("right", filter=mainView)
    def _(event):
        try:
            playback.loop_lock.release()
        except Exception as e:
            pass

    @bindings.add("p", filter=mainView)
    def _(event):
        if playback.paused:
            playback.play()
        else:
            playback.pause()

    @bindings.add("f", filter=mainView)
    def _(event):
        playback.speedup()

    @bindings.add("s", filter=mainView)
    def _(event):
        playback.slowdown()

    @bindings.add("q")
    @bindings.add("c-c")
    def _(event):
        event.app.exit()

    @bindings.add("c-m", filter=mainView)
    def _(event):
        playback.change_playback_mode()

    @bindings.add("c", filter=mainView)
    def _(event):
        # future: add comment
        pass

    @bindings.add("c-f", filter=mainView)
    def _(event):
        # future: flag command
        pass

    @bindings.add("c-s", filter=mainView)
    def _(event):
        time = datetime.datetime.now()
        with open(SAVE_LOCATION + f"_{time.strftime('%Y%m%d%H%M')}", "wb+") as outfi:
            pickle.dump(playback.hist, outfi)

    @bindings.add("g", filter=mainView)
    def _(event):
        # future: goto time
        pass

    @bindings.add("h")
    def _(event):
        # display help screen
        if event.app.displayingHelpScreen:
            # exit help screen
            event.app.displayingHelpScreen = False
            playback.pause()
            event.app.layout = event.app.savedLayout
            event.app.invalidate()

        else:
            # display help screen
            event.app.displayingHelpScreen = True
            event.app.savedLayout = event.app.layout
            event.app.layout = helpLayout
            event.app.invalidate()

    helpLayout = Layout(
        Frame(
            Window(
                FormattedTextControl(
                    "HELP SCREEN\n\n"
                    "h -        help screen\n"
                    "s -        slow down\n"
                    "p -        toggle play/pause\n"
                    "c -        add comment to current command\n"
                    "ctrl-m     change playback mode\n"
                    "ctrl-f     flag event\n"
                    "n/dwn/rght next event\n"
                )
            )
        )
    )

    def toolbar_text():
        """Returns bottom toolbar for app

        Returns
        =======
        _ : prompt_toolkit.formatted_text.HTML
            Text for the bottom toolbar for the app
        """
        if playback.playback_mode == playback.EVENINTERVAL:
            return HTML(
                "<table><tr>"
                f"<th>PLAYBACK TIME: {playback.current_time.strftime('%b %d %Y %H:%M:%S')}</th>     "
                f"<th>PLAYBACK MODE: {playback.playback_mode}</th>    "
                f"<th>PAUSED: {playback.paused}</th>      "
                f"<th>PLAYBACK INTERVAL: {playback.playback_interval}s</th>"
                "</tr></table>"
            )
        else:
            return HTML(
                "<table><tr>"
                f"<th>PLAYBACK TIME: {playback.current_time.strftime('%b %d %Y %H:%M:%S')}</th>     "
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
    toolbar = Window(
        FormattedTextControl(text=toolbar_text),
        height=Dimension(max=1, weight=10000),
        dont_extend_height=True,
    )

    main_view = HSplit([body, toolbar], padding_char="-")

    hspApp.layout = Layout(main_view)
    hspApp.key_bindings = bindings

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
        hspApp.layout.focus(old_command_window)
        hspApp.layout.current_control.text = new_command_window.text
        hspApp.layout.focus(new_command_window)
        hspApp.layout.current_control.text = FormattedText(render_command(command))
        hspApp.invalidate()

    ###################################################
    # Setting Up Loop to async iter over history
    ###################################################

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

    async def redraw_timer():
        """Async method to force a redraw of the app every second

        Never terminates
        # future: do some more checking and error handling
        """
        while True:
            await asyncio.sleep(0.01)
            hspApp.invalidate()

    loop = asyncio.get_event_loop()
    use_asyncio_event_loop()
    try:
        # Run command_loop and hspApp.run_async next to each other
        # future: handle when one completes before the other
        loop.run_until_complete(
            asyncio.gather(
                command_loop(),
                hspApp.run_async().to_asyncio_future(),
                playback.run_async(),
                redraw_timer(),
            )
        )
    finally:
        loop.close()


if __name__ == "__main__":
    main()
