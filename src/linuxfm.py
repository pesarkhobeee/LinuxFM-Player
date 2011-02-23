#!/usr/bin/env python
#-*- coding:utf-8 -*-

__version__ = '0.1.0'

import sys
import os

if sys.platform == 'linux2':
	# Set process name.  Only works on Linux >= 2.1.57.
	try:
		from ctypes import *
		libc = cdll.LoadLibrary('/lib/libc.so.6')
		libc.prctl( 15, 'linuxfm-player', 0, 0, 0) # 15 is PR_SET_NAME
	except:
		pass

import readline
import rlcompleter
import pygtk
pygtk.require('2.0')
import gtk
import glib
import gnomeapplet
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
#import pynotify
import tempfile

from mplayer import MPlayer

class Player(object):
	setting = gtk.settings_get_default()
	setting.set_long_property("gtk-button-images",True,"")
	
	def delete_event(self, widget, event, data=None):
		return False

	def destroy(self, widget, data=None):
		os.close(self.fd)
		os.remove(self.templist)
		self.mp.quit()
		gtk.main_quit()
		
	def on_mediakey(self,comes_from, what):
		""" gets called when multimedia keys are pressed down.
		"""

		if what in ['Stop','Play','Next','Previous']:
			if(what == 'Play'):
				self.play_pause(widget=None)
			elif(what == 'Stop'):
				self.stop(widget=None)
			elif(what == 'Next'):
				self.next(widget=None)
			elif(what == 'Previous'):
				self.previous(widget=None)
		else:
			print ('Got a multimedia key...')

	def play_pause(self, widget, data=None):
		if self.loadlist_flag == "empty" :
			self.run_open_file_dialog(None)
		
		elif self.loadlist_flag == "stop" :
			self.mp.loadlist(self.templist)
			self.loadlist_flag = "play"
			image = gtk.Image()
			image.set_from_stock("gtk-media-pause",gtk.ICON_SIZE_BUTTON)
			self.play_pause_button.set_image(image)
			
		elif self.loadlist_flag == "play" :
			self.mp.pause()
			self.loadlist_flag = "pause"
			image = gtk.Image()
			image.set_from_stock("gtk-media-play",gtk.ICON_SIZE_BUTTON)
			self.play_pause_button.set_image(image)

		elif self.loadlist_flag == "pause" :
			self.mp.pause()
			self.loadlist_flag = "play"
			image = gtk.Image()
			image.set_from_stock("gtk-media-pause",gtk.ICON_SIZE_BUTTON)
			self.play_pause_button.set_image(image)
	
	def play_pause_press(self, widget,event, applet):
		if event.button == 3 :
			applet.emit("button-press-event",event)
			return True

	def stop(self, widget, data=None):
		if self.loadlist_flag != "empty" :
			self.mp.stop()
			self.loadlist_flag = "stop"
			image = gtk.Image()
			image.set_from_stock("gtk-media-play",gtk.ICON_SIZE_BUTTON)
			self.play_pause_button.set_image(image)

	def stop_press(self, widget,event, applet):
		if event.button == 3 :
			applet.emit("button-press-event",event)
			return True

	def seek(self,seek_type):
		if self.ts == False and self.t <= 1:
			self.t = 0
		else :
			self.t += 1
		self.mp.command('seek '+seek_type+' 0')
		return self.ts
		
	def next(self, widget, data=None):
		if self.loadlist_flag != "empty" :
			if self.t <= 1 :
				self.mp.command('pausing_keep_force pt_step 1')
			self.t = 0
			self.ts = False
	
	def next_press(self, widget,event, applet):
		if event.button == 1 and self.loadlist_flag == "play":
			glib.timeout_add(1*1000, self.seek, '+2')
			self.ts = True
		elif event.button == 3 :
			applet.emit("button-press-event",event)
			return True
			

	def previous(self, widget, data=None):
		if self.loadlist_flag != "empty" :
			if self.t <= 1 :
				self.mp.command('pausing_keep_force pt_step -1')
			self.t = 0
			self.ts = False
	
	def previous_press(self, widget,event, applet):
		if event.button == 1 and self.loadlist_flag == "play":
			glib.timeout_add(1*1000, self.seek, '-4')
			self.ts = True
		elif event.button == 3 :
			applet.emit("button-press-event",event)
			return True

	def run_open_file_dialog(self, widget, data=None):
		file_chooser_dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_OPEN)
		file_chooser_dialog.set_select_multiple(True)

		open_button = file_chooser_dialog.add_button(gtk.STOCK_OPEN, gtk.RESPONSE_OK)
		cancel_button = file_chooser_dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

		response = file_chooser_dialog.run()

		if response == gtk.RESPONSE_OK :
			list_file = open(self.templist, "w")
			for fn in file_chooser_dialog.get_filenames():
				list_file.write(fn+'\n')
			list_file.close()
			
			self.mp.loadlist(self.templist)
			self.loadlist_flag = "play"
			image = gtk.Image()
			image.set_from_stock("gtk-media-pause",gtk.ICON_SIZE_BUTTON)
			self.play_pause_button.set_image(image)
			
			#data = self.mp.get_meta_title()
			#for d in self.mp.get_meta_title() :
			#	data += d
			#notify = pynotify.Notification("Title", "dsfjkjdshfkj")
			#notify.show()

		file_chooser_dialog.destroy()
	
	def run_open_location_dialog(self, widget, data=None):
		dialog = gtk.Dialog(title="Open Location")
		dialog.set_border_width(10)
		dialog.set_default_size(400,120)
		cancel_button = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		open_button = dialog.add_button(gtk.STOCK_OPEN, gtk.RESPONSE_OK)
		
		label = gtk.Label("Enter the address of the file you would like to open:")
		label.set_alignment(0.0, 0.50)
		dialog.vbox.pack_start(label, False,True,5)
		
		location = gtk.Entry()
		dialog.vbox.pack_start(location, False,True,0)
		
		dialog.vbox.set_spacing(5)
		dialog.vbox.show_all()
		
		response = dialog.run()
		
		if response == gtk.RESPONSE_OK :
			
			self.mp.loadfile(location.get_text())
			self.loadlist_flag = "play"
			image = gtk.Image()
			image.set_from_stock("gtk-media-pause",gtk.ICON_SIZE_BUTTON)
			self.play_pause_button.set_image(image)
			
			#data = self.mp.get_meta_title()
			#for d in self.mp.get_meta_title() :
			#	data += d
			#notify = pynotify.Notification("Title", "dsfjkjdshfkj")
			#notify.show()
			
		dialog.destroy()
		
	
	def context_menu(self,applet):
		context_menu_xml ="""
				<popup name="button3">
					<menuitem name="File Item" verb="BlahFile" _label="File" pixtype="stock" pixname="gtk-open"/>
					<menuitem name="Open Location Item" verb="BlahOpenLocation" _label="Open Location"/>
					<menuitem name="LinuxFM Item" verb="BlahLinuxFM" _label="LinuxFM" />
					<separator />
					<menuitem name="About Item" verb="BlahAbout" _label="About" pixtype="stock" pixname="gnome-stock-about"/>
				</popup>
			"""
		
		verbs = [	("BlahFile", self.run_open_file_dialog),
					("BlahOpenLocation", self.run_open_location_dialog),
					("BlahLinuxFM", self.play_linuxfm_stream),
					("BlahAbout", self.display_about_dialog)]
		applet.setup_menu(context_menu_xml, verbs, None)
	
	def play_linuxfm_stream(self,widget, data=None):
		self.mp.command("play -cache 500 http://linuxfm.com:8000/live ")
		self.loadlist_flag = "play"
		image = gtk.Image()
		image.set_from_stock("gtk-media-pause",gtk.ICON_SIZE_BUTTON)
		self.play_pause_button.set_image(image)
		
		#data = self.mp.get_meta_title()
		#for d in self.mp.get_meta_title() :
		#	data += d
		#notify = pynotify.Notification("Title", "Linux FM")
		#notify.show()
		
	def display_about_dialog(self,widget, data=None):
		dialog = gtk.AboutDialog()
		
		dialog.set_name("LinuxFM Player")
		dialog.set_version("0.1a")
		dialog.set_comments("An applet to play Iranian LinuxFM radio stream using mplayer")
		dialog.set_copyright("Copyright © 2011 Farid Ahmadian")
		dialog.set_website_label("LinuxFM")
		dialog.set_website("http://linuxfm.com")
		dialog.set_authors(["Farid Ahmadian <ahmadian@pitm.net>",
							"Mohammad Sadegh At'hari <sadegh.msa@gmail.com>"])

		dialog.run()
		dialog.destroy()
		
	def on_change_background(self, applet, type, color, pixmap):
		applet.set_style(None)
		rc_style = gtk.RcStyle()
		applet.modify_style(rc_style)
		if (type == gnomeapplet.COLOR_BACKGROUND):
			applet.modify_bg(gtk.STATE_NORMAL, color)
		elif (type == gnomeapplet.PIXMAP_BACKGROUND):
			style = applet.style
			style.bg_pixmap[gtk.STATE_NORMAL] = pixmap
			applet.set_style(style)

	def make_window(self,applet,iid):
		applet.connect("change-background", self.on_change_background)

		hbox1 = gtk.HBox(homogeneous=False, spacing=3)

		vbox = gtk.VBox(homogeneous=False, spacing=3)

		self.previous_button = gtk.Button("")
		self.previous_button.set_relief(gtk.RELIEF_NONE)
		image = gtk.Image()
		image.set_from_stock("gtk-media-previous",gtk.ICON_SIZE_BUTTON)
		self.previous_button.set_image(image)
		self.previous_button.connect("clicked",self.previous)
		self.previous_button.connect("button-press-event",self.previous_press,applet)

		hbox1.pack_start(self.previous_button, expand=False, fill=False, padding=0)

		self.stop_button = gtk.Button("")
		self.stop_button.set_relief(gtk.RELIEF_NONE)
		image = gtk.Image()
		image.set_from_stock("gtk-media-stop",gtk.ICON_SIZE_BUTTON)
		self.stop_button.set_image(image)
		self.stop_button.connect("clicked",self.stop)
		self.stop_button.connect("button-press-event",self.stop_press,applet)
		hbox1.pack_start(self.stop_button, expand=False, fill=False, padding=0)

		self.play_pause_button = gtk.Button("")
		self.play_pause_button.set_relief(gtk.RELIEF_NONE)
		image = gtk.Image()
		image.set_from_stock("gtk-media-play",gtk.ICON_SIZE_BUTTON)
		self.play_pause_button.set_image(image)
		self.play_pause_button.connect("clicked",self.play_pause)
		self.play_pause_button.connect("button-press-event",self.play_pause_press,applet)
		hbox1.pack_start(self.play_pause_button, expand=False, fill=False, padding=0)

		self.next_button = gtk.Button("")
		self.next_button.set_relief(gtk.RELIEF_NONE)
		image = gtk.Image()
		image.set_from_stock("gtk-media-next",gtk.ICON_SIZE_BUTTON)
		self.next_button.set_image(image)
		self.next_button.connect("clicked",self.next)
		self.next_button.connect("button-press-event",self.next_press, applet)

		hbox1.pack_start(self.next_button, expand=False, fill=False, padding=0)
		vbox.pack_start(hbox1, expand=False, fill=False, padding=0)
		
		self.context_menu(applet)
		applet.connect("delete_event", self.delete_event)
		applet.connect("destroy", self.destroy)

		applet.add(vbox)
		applet.show_all()

	def __init__(self):
		MPlayer.populate()
		self.mp = MPlayer()

		self.fd,self.templist = tempfile.mkstemp()
		self.loadlist_flag = "empty"
		self.t = 0

		# set up the glib main loop.
		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
		bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		bus_object = bus.get_object('org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon/MediaKeys')

		# this is what gives us the multi media keys.
		dbus_interface='org.gnome.SettingsDaemon.MediaKeys'
		bus_object.GrabMediaPlayerKeys("MyMultimediaThingy", 0, dbus_interface=dbus_interface)

		# connect_to_signal registers our callback function.
		bus_object.connect_to_signal('MediaPlayerKeyPressed', self.on_mediakey)



if __name__ == '__main__':   # testing for execution
	player = Player()
	#player.make_window()
	gnomeapplet.bonobo_factory('OAFIID:LinuxFM_Player_Factory', 
							gnomeapplet.Applet.__gtype__, 
							'LinuxFM Player', '0.1', 
							player.make_window)
