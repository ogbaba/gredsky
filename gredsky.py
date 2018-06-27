#!/usr/bin/env python3

from redskyAPI import SkyChatClient
from time import sleep
from bs4 import BeautifulSoup
from urllib.request import urlopen
import subprocess
import sys
import threading
import gi
import html
import tempfile
import os


gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, GObject, GdkPixbuf

class GtkClient (SkyChatClient):
    def __init__ (self, nickname, pwd, room):
        super().__init__(nickname, pwd, room)
        self.window = Gtk.Window(resizable=False,
                                 has_resize_grip=False)
        self.window.connect("delete-event", Gtk.main_quit)
        
        self._box = Gtk.Box(homogeneous=False,
                            vexpand=True,
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
        self._sw = Gtk.ScrolledWindow(min_content_height=400,
                                      min_content_width=520)
        self._messages = Gtk.TextView(editable=False)#, wrap_mode=Gtk.WrapMode.WORD)
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
        msg_text = msg['pseudo'] + " : "
        #for i in range(0,20):
        soup = BeautifulSoup(html.unescape(msg['message']))
        nb_images = 0
        images = []
        nb_images = 0
        for img in soup.find_all('img'):
            img.replaceWith("#IMG#")
            temp_fic = open(os.path.dirname(os.path.realpath(__file__)) +
                            "/img/" +
                            img['src'].rsplit('/',1)[-1], "wb") #tempfile.NamedTemporaryFile()
            try:
                if img['src'][:4] != "http":
                    print('https:'+img['src'])
                    img_temp = urlopen("https:"+img['src'])
                else:
                    print(img['src'])
                    img_temp = urlopen(img['src'])
            except:
                continue
            temp_fic.write(img_temp.read())
            images.append(temp_fic.name)
            temp_fic.close()
            nb_images += 1
                        
        texte_separe = soup.get_text().split("#IMG#")
        self._buffer = self._messages.get_buffer()
        self._buffer.insert(self._buffer.get_end_iter(), msg_text,-1)
        i = 0
        for s in texte_separe:
            self._buffer.insert(self._buffer.get_end_iter(), s, -1)
            if (nb_images <= 0):
                continue
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(images[i])
            print(images[i])
            self._buffer.insert_pixbuf(self._buffer.get_end_iter(), pixbuf)
            self._buffer.insert(self._buffer.get_end_iter(), " \n", -1)
            i += 1
            
        self._buffer.insert(self._buffer.get_end_iter(), "\n", -1)
        while Gtk.events_pending():
            Gtk.main_iteration()
        pos = self._sw.get_vadjustment()
        pos.set_value(50)
        self._sw.set_vadjustment(pos)
        #fin = self._buffer.create_mark("fin", self._buffer.get_end_iter())
        #self._messages.scroll_to_mark(fin, 0, True, 0.5, 0.5)
        if not self.window.is_active() and self._settings_notify.get_active():
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

