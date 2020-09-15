#--------------------------------------------------------
#		           	   IMPORTS
#--------------------------------------------------------

import os
import requests
import time
import functools
from concurrent import futures
from tkinter import *
from tkinter import filedialog
import tkadv
import zfunctions as z
import obswebsocket
import obswebsocket.requests

#--------------------------------------------------------
#		           	   VARIABLES
#--------------------------------------------------------

config = z.getJson("Login.json")
version = z.read("version.txt")
print(version)
ws = obswebsocket.obsws(config["host"], config["port"], config["password"])
obsConnected = False

bgColor = "#2d2d2d"
bgDarkColor = "#272727"
bgDarkColor2 = "#212121"
fontFamily = "Helvetica"
hoverColor = "#962323"

maskPath = ""
videoPath = ""

#--------------------------------------------------------
#		           	   CLASS
#--------------------------------------------------------

class sceneButton:
	def __init__(self, parent, scene):
		def changeButton():
			change(scene)
		self.Button = Button(parent, text=scene, bg=bgDarkColor, fg="#bbbbbb", font=(fontFamily, 11), command=changeButton, activebackground="#992222", activeforeground="white")
		self.Button.pack(ipadx=25, fill=X, padx=2, pady=2)

#--------------------------------------------------------
#		           	   FUNCTIONS
#--------------------------------------------------------

def getFile():
	global filename
	file = filedialog.askopenfilename(initialdir = "Tournaments", title="Open", filetypes=(("MP4","*.mp4"),("Quick Time","*.mov"),("Webm","*.webm")))
	directory = os.path.split(file)[0]
	filename = os.path.split(file)[1]
	inputFile = directory+"\\"+filename
	return inputFile

def setMask():
	global maskPath
	global config

	maskPath = getFile()
	config["mask"] = filename
	z.saveJson("Login.json", config)
	maskDirLabel["text"] = "..."+config["mask"][-14:]
	ws.call(obswebsocket.requests.SetSourceSettings("Scene mask", {"local_file": maskPath}))

def setVideo():
	global videoPath
	global config

	videoPath = getFile()
	config["video"] = filename
	z.saveJson("Login.json", config)
	videoDirLabel["text"] = "..."+config["video"][-14:]
	ws.call(obswebsocket.requests.SetSourceSettings("Scene reveal", {"local_file": videoPath}))

#--------------------------------------------------------
#		           	   OBS
#--------------------------------------------------------

def obsConnect():
	global obsConnected
	global config
	global ws
	global obsSettings

	try:
		ws = obswebsocket.obsws(hostEntry.get(), portEntry.get(), passEntry.get())
		ws.connect()
		obsConnected = True
		rootL.pack_forget()
		root.pack()

		obsReg(obsExit, "Exiting")
		scenes = []
		for scene in ws.call(obswebsocket.requests.GetSceneList()).__dict__["datain"]["scenes"]:
			if scene["name"] != "Scene changer":
				if scene["name"] == "-----------------------------------------------":
					break
				else:
					scenes.append(scene["name"])

		for scene in scenes:
			sceneButton(scenesFrame, scene)

		config["host"] = hostEntry.get()
		config["port"] = portEntry.get()
		config["password"] = passEntry.get()
		z.saveJson("Login.json", config)
		maskDirLabel["text"] = "..."+config["mask"][-14:]
		videoDirLabel["text"] = "..."+config["video"][-14:]
		#profile =  ws.call(obswebsocket.requests.GetCurrentSceneCollection()).__dict__["datain"]["sc-name"]
		#obsSettings = z.getJson(os.getenv('APPDATA')+"/obs-studio/basic/scenes/"+profile+".json")
		tk.center()
	except obswebsocket.exceptions.ConnectionFailure as result:
		if str(result) == "Authentication Failed.":
			print("Authentication Failed")
			connectionResultLabel["text"] = "Auth Failed"
		elif str(result)[1:15] == "WinError 10061":
			print("OBS Closed")
			connectionResultLabel["text"] = "OBS Closed"
		obsConnected = False

def currentScene():
	scene = ws.call(obswebsocket.requests.GetCurrentScene()).__dict__["datain"]["name"]
	return scene

def getSourceSettings(source):
	return ws.call(obswebsocket.requests.GetSourceSettings(source)).__dict__["datain"]["sourceSettings"]

def setSourceSettings(source, settings):
	ws.call(obswebsocket.requests.SetSourceSettings(source, settings))

def change(scene):
	setSourceSettings("Previous scene", {"Source.Mirror.Source": currentScene()})
	setSourceSettings("Current scene", {"Source.Mirror.Source": scene})
	ws.call(obswebsocket.requests.SetCurrentScene("Scene changer"))
	ws.call(obswebsocket.requests.SetSceneItemRender("Scene reveal", True, "Scene changer"))
	ws.call(obswebsocket.requests.SetSceneItemRender("Scene mask", True, "Scene changer"))
	ws.call(obswebsocket.requests.SetSceneItemRender("Current scene", True, "Scene changer"))
	time.sleep(3)
	ws.call(obswebsocket.requests.SetCurrentScene(scene))
	ws.call(obswebsocket.requests.SetSceneItemRender("Scene mask", False, "Scene changer"))
	ws.call(obswebsocket.requests.SetSceneItemRender("Scene reveal", False, "Scene changer"))
	ws.call(obswebsocket.requests.SetSceneItemRender("Current scene", False, "Scene changer"))

def obsReg(function, event):
	ws.register(obsExit, eval("obswebsocket.events."+event))

#------- EVENTS -------

def obsExit(message):
	print("exit")
	connectionResultLabel["text"] = "OBS Closed"
	root.pack_forget()
	rootL.pack(anchor="w", padx=10, pady=10)

#--------------------------------------------------------
#		           	   EXECUTION
#--------------------------------------------------------

tk = tkadv.window("OBS-Zn changer - v"+version)

#------- LOGGING -------

rootL = Frame(tk.content, bg=bgColor)
rootL.pack(anchor="center", padx=10, pady=10)

Label(rootL, text="OBS WebSocket", bg=bgColor, fg="#bbbbbb", font=(fontFamily, 13), anchor="w").pack()
Frame(rootL, bg=bgColor).pack(pady=2)
tkadv.horizontalLine(rootL)
Frame(rootL, bg=bgColor).pack(pady=2)

hostFrame = Frame(rootL, bg=bgColor)
hostFrame.pack(anchor="w")
Label(hostFrame, text="Host", bg=bgColor, fg="#bbbbbb", font=(fontFamily, 13), width=5, anchor="w").pack(side=LEFT)
hostEntry = Entry(hostFrame, font=(fontFamily, 13), width=15, bd=0, bg=bgDarkColor2, fg="#bbbbbb", selectbackground="black", insertbackground="white")
hostEntry.pack(side=LEFT)
hostEntry.insert(0, config["host"])

portFrame = Frame(rootL, bg=bgColor)
portFrame.pack(anchor="w")
Label(portFrame, text="Port", bg=bgColor, fg="#bbbbbb", font=(fontFamily, 13), width=5, anchor="w").pack(side=LEFT)
portEntry = Entry(portFrame, font=(fontFamily, 13), width=15, bd=0, bg=bgDarkColor2, fg="#bbbbbb", selectbackground="black", insertbackground="white")
portEntry.pack(side=LEFT)
portEntry.insert(0, config["port"])

passwordFrame = Frame(rootL, bg=bgColor)
passwordFrame.pack(anchor="w")
Label(passwordFrame, text="Pass", bg=bgColor, fg="#bbbbbb", font=(fontFamily, 13), width=5, anchor="w").pack(side=LEFT)
passEntry = Entry(passwordFrame, show="•", font=(fontFamily, 13), width=15, bd=0, bg=bgDarkColor2, fg="#bbbbbb", selectbackground="black", insertbackground="white")
passEntry.pack(side=LEFT)
passEntry.insert(0, config["password"])

Frame(rootL, bg=bgColor).pack(pady=2)
tkadv.horizontalLine(rootL)
Frame(rootL, bg=bgColor).pack(pady=2)

connectFrame = Frame(rootL, bg=bgColor)
connectFrame.pack(anchor="w", padx=2, pady=2)
connectButton = Button(connectFrame, text="Connect", command=obsConnect, bg=bgDarkColor, fg="#bbbbbb", font=(fontFamily, 11), width=9, activebackground="#992222", activeforeground="white")
connectButton.pack(side=LEFT)
connectionResultLabel = Label(connectFrame, bg=bgColor, fg="#dd2222", font=(fontFamily, 11))
connectionResultLabel.pack(side=LEFT, padx=5)

#------- CORE -------

root = Frame(tk.content, bg=bgColor)
#root.pack()

settingsFrame = Frame(root, bg=bgColor)
settingsFrame.pack(padx=10, pady=10, fill=X)

maskFrame = Frame(settingsFrame, bg=bgColor)
maskFrame.pack(fill=X)
Button(maskFrame, text="Mask", command=setMask, bg=bgDarkColor, fg="#bbbbbb", font=(fontFamily, 11), width=5, activebackground="#992222", activeforeground="white").pack(padx=2, pady=2, side=LEFT)
maskDirLabel = Label(maskFrame, text="...", bg=bgColor, fg="#bbbbbb", font=(fontFamily, 11))
maskDirLabel.pack(side=LEFT)

videoFrame = Frame(settingsFrame, bg=bgColor)
videoFrame.pack(fill=X)
Button(videoFrame, text="Video", command=setVideo, bg=bgDarkColor, fg="#bbbbbb", font=(fontFamily, 11), width=5, activebackground="#992222", activeforeground="white").pack(padx=2, pady=2, side=LEFT)
videoDirLabel = Label(videoFrame, text="...", bg=bgColor, fg="#bbbbbb", font=(fontFamily, 11))
videoDirLabel.pack(side=LEFT)

tkadv.horizontalLine(root)
scenesFrame = Frame(root, bg=bgColor)
scenesFrame.pack(anchor="w", padx=10, pady=10)
Label(scenesFrame, text="Scenes", bg=bgColor, fg="#bbbbbb", font=(fontFamily, 15)).pack(anchor="w")

tk.center()
root.mainloop()
