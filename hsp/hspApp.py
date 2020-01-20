"""Example App for controlling and displaying a playback object

Takes a playback object and creates the app that can be run synchronously or asynchronously

Author: starksimilarity@gmail.com
"""
import aio_pika
import asyncio
from collections import deque
from contextlib import contextmanager
import datetime
from functools import partial
import json
import pickle
import pika

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout import Layout, Dimension
from prompt_toolkit.widgets import Box, Frame, TextArea
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar

SAVE_LOCATION = "SavedPlayback"


class HspApp(Application):
    """prompt_toolkit application for controlling and displaying a high-speed playback

    Attributes
    ==========
    displayingHelpScreen : bool
        used to toggle between help screen and normal view
    disabled_bindings : bool
        used to toggle key_bindings
    save_location : str
        Name preamble used when saving playback files
    playback : hsp.Playback
        Playback object that is being controlled by the app
    command_cache : collections.deque
        Local reference to the most recent command objects from playback hist
    main_view : prompt_toolkit.layout.containers.HSplit
        main layout for the app

        

    Methods
    =======
    mainViewCondition()
    init_bindings(self, bindings)
        Adds custom key_bindings to the app
    toolbar_text(self)
        Returns bottom toolbar for app
    render_command(self, command)
        Return string of command object specific to this UI
    get_user_comment(self)
        Modifies the display to add an area to enter a comment for a command
    _set_user_comment(self, buff)
        Callback fuction from the BufferControl created for user comments
    update_display
        displays last N commands in the local cache


    Async Methods
    =============
    msg_consumer(self, loop)
        Primary loop for receiving/displaying commands from playback
    redraw_timer(self)
        Async method to force a redraw of the app every hundreth second
    """

    def __init__(self, save_location=None, *args, **kwargs):

        self.mainViewCondition = partial(self.mainView, self)
        self.mainViewCondition = Condition(self.mainViewCondition)
        self.disabled_bindings = False
        bindings = KeyBindings()
        self.init_bindings(bindings)

        super().__init__(
            full_screen=True, key_bindings=bindings, mouse_support=True, *args, **kwargs
        )

        self.displayingHelpScreen = (
            False
        )  # used to toggle between help screen on normal

        if save_location:
            self.save_location = save_location
        else:
            self.save_location = SAVE_LOCATION
        self._savedLayout = Layout(Window())
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

        ##########################################
        ### Setting up command_queue
        ##########################################
        self.conn = pika.BlockingConnection(pika.ConnectionParameters("172.17.0.2"))
        self.cmd_queue = self.conn.channel()
        self.cmd_queue.queue_declare("commands")

    async def event_received(self, msg):
        """Callback method when aio-pika receives a message
        """
        new_command = json.loads(msg.body)
        self.command_cache.append(new_command)

    @staticmethod
    def mainView(self):
        """Return if app is in main view.

        Returns
        =======
        _ : bool
            If app is not displaying the Help Screen or comment, it's in main view
        """
        disable = self.displayingHelpScreen or self.disabled_bindings
        return not disable

    @contextmanager
    def switched_layout(self):
        """Context manager to stores and restore the current layout

        Saves the current layout to an instance variable and then restores
        that layout on __exit__
        """
        self._saved_layout = self.layout
        yield
        self.layout = self._saved_layout
        self.invalidate()

    @contextmanager
    def paused_playback(self):
        """Context manager for pausing playback temporarily 

        Pauses the playback in the __enter__ section.  If the playback was
        originally paused, the __exit__ section will keep the playback paused,
        otherwise it will resume play of the playback

        #TODO: Rework this to support the microservice arch.
        """
        """
        _originally_paused = self.playback.paused
        #self.playback.pause()
        self.cmd_queue.basic_publish(
                exchange="", routing_key="commands", body="pause"
        )
        #RMQ: Publish pause command
        yield
        if not _originally_paused:
            #self.playback.play()
            self.cmd_queue.basic_publish(
                    exchange="", routing_key="commands", body="play"
            )
            #RMQ: Publish play command
        """
        pass
        yield


    @contextmanager
    def bindings_off(self):
        """Context manager for disabling key_bindings for a given scope

        Sets disabled_bindings to True so that the mainView Condition
        will return False.  Upon __exit__, it returns the key_ binding state
        to what is was when it entered.
        """
        _originally_disabled = self.disabled_bindings
        self.disabled_bindings = True
        yield
        self.disabled_bindings = _originally_disabled

    def init_bindings(self, bindings):
        """Adds custom key_bindings to the app

        #TODO: Look into how publishing to the cmd_queue could be 
                done async. If there's too much latency caused by this
                blocking write to the cmd_queue, it should be removed.
        """

        @bindings.add("n", filter=self.mainViewCondition)
        @bindings.add("down", filter=self.mainViewCondition)
        @bindings.add("right", filter=self.mainViewCondition)
        def _(event):
            try:
                #self.playback.loop_lock.release()
                self.cmd_queue.basic_publish(
                    exchange="", routing_key="commands", body="release"
                )

            except Exception as e:
                pass

        @bindings.add("p", filter=self.mainViewCondition)
        def _(event):
            """TODO: Add back in logic to detect if the playback is
            currently paused and make this a toggle
            """
            self.cmd_queue.basic_publish(
                exchange="", routing_key="commands", body="play"
            )
            """
            else:
                self.cmd_queue.basic_publish(
                    exchange="", routing_key="commands", body="pause"
                )
                #RMQ: Publish pause command
            """

        @bindings.add("f", filter=self.mainViewCondition)
        def _(event):
            #self.playback.speedup()
            self.cmd_queue.basic_publish(
                exchange="", routing_key="commands", body="speedup"
            )
            #RMQ: Publish speedup command

        @bindings.add("s", filter=self.mainViewCondition)
        def _(event):
            #self.playback.slowdown()
            self.cmd_queue.basic_publish(
                exchange="", routing_key="commands", body="slowdown"
            )
            #RMQ: Publish slowdown command

        @bindings.add("q")
        @bindings.add("c-c")
        def _(event):
            event.app.exit()

        @bindings.add("c-m", filter=self.mainViewCondition)
        def _(event):
            #self.playback.change_playback_mode()
            self.cmd_queue.basic_publish(
                exchange="", routing_key="commands", body="cyclemode"
            )
            #RMQ: Publish change playback mode command

        @bindings.add("c", filter=self.mainViewCondition)
        def _(event):
            self.get_user_comment()
            self.update_display()

        @bindings.add("c-f", filter=self.mainViewCondition)
        def _(event):
            # set the flag in both the self.playback and the local cache for display
            #self.playback.flag_current_command()
            self.cmd_queue.basic_publish(
                exchange="", routing_key="commands", body="flag"
            )
            #RMQ: Publish flag_current command
            self.update_display()

        @bindings.add("c-s", filter=self.mainViewCondition)
        def _(event):
            time = datetime.datetime.now()
            with open(
                self.save_location + f"_{time.strftime('%Y%m%d%H%M')}", "wb+"
            ) as outfi:
                pickle.dump(self.playback.hist, outfi)

        @bindings.add("g", filter=self.mainViewCondition)
        def _(event):
            # future: goto time
            pass

        @bindings.add("h")
        def _(event):
            # display help screen
            if event.app.displayingHelpScreen:
                # exit help screen
                event.app.displayingHelpScreen = False
                #self.playback.pause()
                self.cmd_queue.basic_publish(
                    exchange="", routing_key="commands", body="pause"
                )
                #RMQ: Publish pause command
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
                    "g -        goto specific time in history\n"
                    "ctrl-m     change self.playback mode\n"
                    "ctrl-f     flag event\n"
                    "ctrl-s     save playback object to file\n"
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
        """
        #Going to have to replace a lot of this text with either local vars or pull from msg_queue
        if self.playback.playback_mode == self.playback.EVENINTERVAL:
            #RMQ: May have to store this state locally
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
        """
        return HTML("Working on this")
    
    def render_command(self, command):
        """Return string of command object specific to this UI

        Parameters
        ==========
        command : dict
            Dict containing components of a command

        Returns
        =======
        _ : str
            String representation of Command object
        """
        try:
            if command.get("flagged", "False") == "True":
                color = "ansired"
            else:
                color = "ansiwhite"
        except:
            color = "ansiwhite"
        try:
            return [
                ("bg:ansiblue ansiwhite", f"{command.get('time', '')}\n"),
                (
                    color,
                    (
                        f"{command.get('hostUUID', 'Unknown Host')}:"
                        f"{command.get('user', 'Unknown User')} > "
                        f"{command.get('command', 'Unknown Command')}\n"
                        f"{command.get('result', 'Unknown Result')}\n"
                        f"{command.get('comment','')}"
                    ),
                ),
            ]
        except Exception as e:
            # All of the command.get code about should fail gracefully...
            # but just in case, we can have it rendered in the window anyway
            return [(color, str(command))]

    def get_user_comment(self):
        """Modifies the display to add an area to enter a comment for a command

        Creates a BufferControl in a Frame and replaces the toolbar with the Frame

        #bug: the new toolbar is unable to get focus right away; it requires the user to click 
                in the area
        """
        self._savedLayout = self.layout
        self.disabled_bindings = True
        commentControl = BufferControl(
            Buffer(accept_handler=self._set_user_comment), focus_on_click=True
        )
        user_in_area = Frame(
            Window(
                commentControl,
                height=Dimension(max=1, weight=10000),
                dont_extend_height=True,
            ),
            title="Enter Comment (alt-Enter to submit)",
        )

        self.toolbar = user_in_area
        self.main_view = HSplit([self.body, self.toolbar], padding_char="-")
        self.layout = Layout(self.main_view, focused_element=user_in_area.body)
        self.layout.focus(user_in_area.body)
        self.invalidate()

    def _set_user_comment(self, buff):
        """Callback fuction from the BufferControl created for user comments

        Takes the user comment and sets that as the current command's comment.
        Then replaces the original layout.
        """
        #self.playback.hist[self.playback.playback_position - 1].comment = buff.text
        self.cmd_queue.basic_publish(
                exchange="", routing_key="commands", body=f"comment: {buff.text}"
        )
        #RMQ: Publish comment
        self.disabled_bindings = False
        self.layout = self._savedLayout
        self.update_display()
        self.invalidate()

    def update_display(self):
        """displays last N commands in the local cache

        This should only be called when the main display with command history is showing
        otherwise the requisite windows will not be focusable.

        #future: allow the number of commands displayed to grow to the size of the 
                available screen realastate
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

    async def msg_consumer(self, event_loop):
        """Primary loop for receiving/displaying commands from playback

        Asynchronously consume messages from msg_queue.  The playback object
        publishes events to the msg_queue asynchronously depending on the 
        playback mode.
        Takes the command object and displays it to the screen
        """
        # give this thread control over playback for manual mode
        # lock is released by certain key bindings
        conn = await aio_pika.connect("amqp://guest:guest@172.17.0.2/")
        channel = await conn.channel()
        msg_queue = await channel.declare_queue("messages")
        #await self.playback.loop_lock.acquire() # This goes away when using RMQ

        while True:
            await msg_queue.consume(self.event_received)
            #if self.playback.playback_mode == "MANUAL":
            #    await self.playback.loop_lock.acquire()
                #This goes away when using RMQ
            self.update_display()

    async def redraw_timer(self):
        """Async method to force a redraw of the app every hundreth second

        Never terminates
        # future: do some more checking and error handling
        """
        while True:
            await asyncio.sleep(0.01)
            self.invalidate()
