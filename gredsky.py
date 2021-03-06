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
import requests
import json
import math
import random

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, GObject, GdkPixbuf, GLib


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
        self._box_middle = Gtk.Box(homogeneous=False,
                                    hexpand=False,
                                    vexpand=False,
                                    orientation=Gtk.Orientation.HORIZONTAL,
                                    spacing=4)
        self._settings_notify = Gtk.CheckButton(label="Notifications")
        self._box_top.add(self._settings_notify)
        self._box.add(self._box_top)
        self._send_btn = Gtk.Button(label="Envoyer")
        self._sw = Gtk.ScrolledWindow(min_content_height=480,
                                      min_content_width=540)
        self._sw_users = Gtk.ScrolledWindow(min_content_height=480,
                                            min_content_width=220)
          
        self._messages = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD)
        self._users_view = Gtk.TextView(editable=False)
        self._input = Gtk.Entry()
        self._box_bottom.add(self._input)
        self._box_bottom.add(self._send_btn)
        self._box_middle.pack_start(self._sw, True, True, 8)
        self._box_middle.pack_start(self._sw_users, True, True, 8)
        self._send_btn.connect("clicked", self.on_send_message_clicked,
                               self._input)
        self._input.connect("activate", self.on_send_message_clicked,
                            self._input)
        self._sw.add(self._messages)
        self._sw_users.add(self._users_view)
        self._box.add(self._box_middle)
        self._box.add(self._box_bottom)        
        self.window.add(self._box)
        self._msg_text = ""
        self._notify = True
        self.window.show_all()
        self._buffer = self._messages.get_buffer()

        
    def on_login (self):
        sleep(2)

    def on_message (self, msg):
        #while Gtk.events_pending():
        #    Gtk.main_iteration()
        msg_text = "\n" + msg['pseudo'] + " : "
        end_iter = self._buffer.get_end_iter()

        #### CAS PARTICULIERS
        
        ### le bot qui fout la merde
        if msg['pseudo'] == 'RedSkyBot':
            msg_text = msg_text
            msg_text += html.unescape(msg['message'])
            GLib.idle_add(self._buffer.insert, end_iter, msg_text, -1)
            return
        ### les stickers
        print(msg['message'])
        #if msg['message'].startswith(" https://api.risibank.fr"):
        #    msg['message'] = "<img src=\"" + msg['message'][1:] + "\">"

        soup = BeautifulSoup(html.unescape(msg['message']), "lxml")
        images = []
        nb_images = 0
        for img in soup.find_all('img'):
            img.replaceWith("#IMG#")
            #if os.path.isfile(img['src'].rsplit('/',1)[-1]):
            #    continue
            temp_fic = open(os.path.dirname(os.path.realpath(__file__)) +
                            "/img/" +
                            img['src'].rsplit('/',1)[-1], "wb") #tempfile.NamedTemporaryFile()
            try:
                print(img['src'])
                if img['src'].startswith("//api.risibank.fr"):
                    print("stick")
                    img_temp = urlopen("https:"+img['src'])
                else:
                    img_temp = urlopen("https:"+img['src'])

#                else if img['src'].startswith("//api.risibank.fr"):
#                    #print(img['src'])
#                    img_temp = urlopen(img['src'])
            except IOError as e:
                print("erreur : " +str(e))
                continue
            temp_fic.write(img_temp.read())
            images.append(temp_fic.name)
            temp_fic.close()
            nb_images += 1
                        
        texte_separe = soup.get_text().split("#IMG#")
        #GLib.idle_add(self._buffer.insert, end_iter, "\n", -1)
        GLib.idle_add(self._buffer.insert, end_iter, msg_text,-1)
        i = 0
        for s in texte_separe:
            GLib.idle_add(self._buffer.insert, end_iter, s, -1)
            #print(s)
            if (nb_images > 0):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(images[i], width=136, height=102, preserve_aspect_ratio=True)
                GLib.idle_add(self._buffer.insert_pixbuf, 
                        end_iter, pixbuf)
                i += 1
                nb_images = nb_images - 1
        GLib.idle_add(self._messages.scroll_to_iter, 
                end_iter, 0, False, 0.5, 0.5)
        if not self.window.is_active() and self._settings_notify.get_active():
            subprocess.Popen(['notify-send',msg['pseudo'] + ' : '
                              + html.unescape(msg['message'])])

    def on_send_message_clicked(self, widget, entry):
        # on gère le risibanquisme
        msg = entry.get_text()
        if msg[0] == '#':
            self.msgsend(recherche_risibank(msg[1:]))
        else:
            self.msgsend(msg)
        GLib.idle_add(entry.set_text, "")
    
    def calmos(self):
        while Gtk.events_pending():
            Gtk.main_iteration()
            
    def on_connected_list(self, msg):
        #print(msg)
        buf_users = self._users_view.get_buffer()
        users = ""
        for p in msg["list"]:
            temps = int(p["last_activity"]) 
            temps_str = "LONGTEMPS"
            if temps < 60:
                temps_str = "<1m"
            elif temps < 600:
                temps_str = str(int(temps/60)) + "m"
            else:
                temps_str = ">10m"
            users += p["pseudo"] + " (" + temps_str +")\n"
        GLib.idle_add(buf_users.set_text, users)


def recherche_risibank (recherche):
    r = requests.post('https://api.risibank.fr/api/v0/search', data={'search': recherche})
    j = json.loads(r.text)
    id = random.choice(j['stickers'])['id']
    #print('https://api.risibank.fr/cache/stickers/d' + str(math.floor(id / 100)) + "/" + str(id) + "-full.png")
    return 'https://api.risibank.fr/cache/stickers/d' + str(math.floor(id / 100)) + "/" + str(id) + "-full.png"

config_path = os.path.join(os.path.dirname(__file__), 'config.txt')
with open(config_path) as f:
    infos_connexion =  f.readline().strip().split(' ')
    mdp = infos_connexion[1]
    pseudo = infos_connexion[0]

c = GtkClient(pseudo,mdp,0)
GObject.threads_init()
thread = threading.Thread(target=c.run)
thread.daemon = True
thread.start()
Gtk.main()

