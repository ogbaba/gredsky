#!/usr/bin/env python3

from redskyAPI import SkyChatClient
from time import sleep
import subprocess
import sys
import threading
import gi
import html
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2
from gi.repository import Gtk, GLib, GObject

class GtkClient (SkyChatClient):
    def __init__ (self, nickname, pwd, room):
        super().__init__(nickname, pwd, room)
        self.window = Gtk.Window(resizable=False,
                                 has_resize_grip=False)
        self.window.connect("delete-event", Gtk.main_quit)
        
        self._box = Gtk.Box(homogeneous=False,
                            expand=True,
                            hexpand=True,
                           orientation=Gtk.Orientation.VERTICAL,
                           spacing=6)
        self._box_bottom = Gtk.Box(homogeneous=True,
                                   hexpand=False,
                                   vexpand=True,
                                   spacing=4)
        self._box_top = Gtk.Box(homogeneous=True,
                                   hexpand=False,
                                   vexpand=True,
                                   spacing=4)
        self._settings_notify = Gtk.CheckButton(label="Notifications")
        self._box_top.add(self._settings_notify)
        self._box.add(self._box_top)
        self._send_btn = Gtk.Button(label="Envoyer")
        self._sw = Gtk.ScrolledWindow(hexpand=False,
                                      min_content_height=400,
                                      min_content_width=520)
        self._messages = WebKit2.WebView(editable=False)
        self._input = Gtk.Entry()
        self._box_bottom.add(self._input)
        self._box_bottom.add(self._send_btn)
        self._send_btn.connect("clicked", self.on_send_message_clicked,
                               self._input)
        self._input.connect("activate", self.on_send_message_clicked,
                            self._input)
        self._sw.add(self._messages)
        self._box.add(self._sw)
        self._box.add(self._box_bottom)        
        self.window.add(self._box)
        self._msg_text = ""
        self._notify = True
        self.window.show_all()

        
    def on_login (self):
        sleep(2)

    def on_message (self, msg):
        self._msg_text +=  "<b>" + msg['pseudo'] + "</b> : "
        self._msg_text += msg['message'] + "<br>"
        self._messages.load_html(self._msg_text, 'http://redsky.fr')
        self._sw.set_placement(Gtk.CornerType.BOTTOM_LEFT)
        if not self.window.is_active() and self._settings_notify.toggled:
            print("test pas actif")
            subprocess.Popen(['notify-send',msg['pseudo'] + ' : '
                              + html.unescape(msg['message'])])

    def on_send_message_clicked(self, widget, entry):
        self.msgsend(entry.get_text())
        entry.set_text("")
    

if (len(sys.argv) != 4):
    print("Utilisation : ./" + sys.argv[0] + " pseudo mdp salon \n")
    exit()
c = GtkClient(sys.argv[1],sys.argv[2], int(sys.argv[3]))
GObject.threads_init()
thread = threading.Thread(target=c.run)
thread.daemon = True
thread.start()
Gtk.main()

