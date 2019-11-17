"""Example UI for creating and controlling a playback object

Creates a playback object and a prompt_toolkit Application and runs
each asynchronously.

Author: starksimilarity@gmail.com
"""

import asyncio
from collections import deque
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

SAVE_LOCATION = "SavedPlayback"


class HspApp(Application):
    def __init__(self, playback, save_location=None, *args, **kwargs):

        bindings = KeyBindings()
        self.init_bindings(bindings)

        super().__init__(full_screen=True, key_bindings=bindings, *args, **kwargs)

        self.displayingHelpScreen = (
            False
        )  # used to toggle between help screen on normal

        if save_location:
            self.save_location = save_location
        else:
            self.save_location = SAVE_LOCATION
        self.playback = playback
        self.savedLayout = Layout(Window())
        self.command_cache = deque([], maxlen=5)

        ##########################################
        ### Setting up views
        ##########################################

        self.old_command_window = FormattedTextControl(
            text="Output goes here", focusable=True
        )
        self.new_command_window = FormattedTextControl(
            text="Output goes here", focusable=True
        )

        self.body = Frame(
            HSplit(
                [
                    Frame(Window(self.old_command_window)),
                    Frame(Window(self.new_command_window)),
                ]
            )
        )
        self.toolbar = Window(
            FormattedTextControl(text=self.toolbar_text),
            height=Dimension(max=1, weight=10000),
            dont_extend_height=True,
        )

        self.main_view = HSplit([self.body, self.toolbar], padding_char="-")
        self.layout = Layout(self.main_view)

    def mainView(self):
        """Return if app is in main view.

        Returns
        =======
        _ : bool
            If app is not displaying the Help Screen, it's in main view
        """
        # return not self.displayingHelpScreen
        return True

    def init_bindings(self, bindings):
        @bindings.add("n", filter=dummyFilter)
        @bindings.add("down", filter=dummyFilter)
        @bindings.add("right", filter=dummyFilter)
        def _(event):
            try:
                self.playback.loop_lock.release()
            except Exception as e:
                pass

        @bindings.add("p", filter=dummyFilter)
        def _(event):
            if self.playback.paused:
                self.playback.play()
            else:
                self.playback.pause()

        @bindings.add("f", filter=dummyFilter)
        def _(event):
            self.playback.speedup()

        @bindings.add("s", filter=dummyFilter)
        def _(event):
            self.playback.slowdown()

        @bindings.add("q")
        @bindings.add("c-c")
        def _(event):
            event.app.exit()

        @bindings.add("c-m", filter=dummyFilter)
        def _(event):
            self.playback.change_playback_mode()

        @bindings.add("c", filter=dummyFilter)
        def _(event):
            # future: add comment
            pass

        @bindings.add("c-f", filter=dummyFilter)
        def _(event):
            # set the flag in both the self.playback and the local cache for display
            self.playback.flag_current_command()
            self.update_display()

        @bindings.add("c-s", filter=dummyFilter)
        def _(event):
            time = datetime.datetime.now()
            with open(
                self.save_location + f"_{time.strftime('%Y%m%d%H%M')}", "wb+"
            ) as outfi:
                pickle.dump(self.playback.hist, outfi)

        @bindings.add("g", filter=dummyFilter)
        def _(event):
            # future: goto time
            pass

        @bindings.add("h")
        def _(event):
            # display help screen
            if event.app.displayingHelpScreen:
                # exit help screen
                event.app.displayingHelpScreen = False
                self.playback.pause()
                event.app.layout = event.app.savedLayout
                event.app.invalidate()

            else:
                # display help screen
                event.app.displayingHelpScreen = True
                event.app.savedLayout = event.app.layout
                event.app.layout = self.helpLayout
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
                    "ctrl-m     change self.playback mode\n"
                    "ctrl-f     flag event\n"
                    "n/dwn/rght next event\n"
                )
            )
        )
    )

    def toolbar_text(self):
        """Returns bottom toolbar for app

        Returns
        =======
        _ : prompt_toolkit.formatted_text.HTML
            Text for the bottom toolbar for the app
        """
        if self.playback.playback_mode == self.playback.EVENINTERVAL:
            return HTML(
                "<table><tr>"
                f"<th>PLAYBACK TIME: {self.playback.current_time.strftime('%b %d %Y %H:%M:%S')}</th>     "
                f"<th>PLAYBACK MODE: {self.playback.playback_mode}</th>    "
                f"<th>PAUSED: {self.playback.paused}</th>      "
                f"<th>PLAYBACK INTERVAL: {self.playback.playback_interval}s</th>"
                "</tr></table>"
            )
        else:
            return HTML(
                "<table><tr>"
                f"<th>PLAYBACK TIME: {self.playback.current_time.strftime('%b %d %Y %H:%M:%S')}</th>     "
                f"<th>PLAYBACK MODE: {self.playback.playback_mode}</th>    "
                f"<th>PAUSED: {self.playback.paused}</th>      "
                f"<th>PLAYBACK RATE: {self.playback.playback_rate}</th>"
                "</tr></table>"
            )

    def render_command(self, command):
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

    def update_display(self):
        """displays last N commands in the local cache
        """

        self.layout.focus(self.old_command_window)
        if len(self.command_cache) > 1:
            self.layout.current_control.text = self.render_command(
                self.command_cache[-2]
            )
        else:
            self.layout.current_control.text = "COMMAND OUTPUT HERE"
        # self.layout.current_control.text = new_command_window.text
        self.layout.focus(self.new_command_window)
        if len(self.command_cache) > 0:
            self.layout.current_control.text = self.render_command(
                self.command_cache[-1]
            )
        else:
            self.layout.current_control.text = "COMMAND OUTPUT HERE"
        self.invalidate()

    ###################################################
    # Setting Up Loop to async iter over history
    ###################################################

    async def command_loop(self):
        """Primary loop for receiving/displaying commands from playback

        Asynchronously iterates over the Command objects in the playback's history.
        Takes the command object and displays it to the screen
        """
        # give this thread control over playback for manual mode
        # lock is released by certain key bindings
        await self.playback.loop_lock.acquire()
        async for command in self.playback:
            if self.playback.playback_mode == "MANUAL":
                # regain the lock for MANUAL mode
                await self.playback.loop_lock.acquire()

            self.command_cache.append(command)
            # Update text in windows
            self.update_display()
        else:
            # future: fix
            self.command_cache.append(command)
            self.update_display()

    async def redraw_timer(self):
        """Async method to force a redraw of the app every second

        Never terminates
        # future: do some more checking and error handling
        """
        while True:
            await asyncio.sleep(0.01)
            self.invalidate()


@Condition
def dummyFilter():
    return True
