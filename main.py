'''
Application in Kivy to show the operation of updating the firmware of an Arduino board in python.
'''

from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp

import threading
from queue import Queue

from intelhex import IntelHex
from arduinobootloader import ArduinoBootloader


KV = '''
Screen:
    MDBoxLayout:
        orientation:"vertical"
        padding:10
        spacing:10
            
        MDBoxLayout:
            orientation:"horizontal"
            padding:10
            spacing:10
            
            MDLabel:
                text:"Software Version"
            MDLabel:
                id:sw_version
                text:"--"
                
        MDBoxLayout:
            orientation:"horizontal"
            padding:10
            spacing:10
            
            MDLabel:
                text:"Hardware Version"
            MDLabel:
                id:hw_version
                text:"--"
       
        MDBoxLayout:
            orientation:"horizontal"
            padding:10
            spacing:10
            
            MDLabel:
                text:"CPU Name"
            MDLabel:
                id:cpu_version
                text:"--"
                         
        MDBoxLayout:
            orientation:"horizontal"
            padding:10
            spacing:10
            
            MDLabel:
                text:"File information"
            MDLabel:
                id:file_info
                text:"--"
        BoxLayout:
            padding: "10dp"
            orientation: "horizontal"
            MDProgressBar:
                id: progress
                value: 0
                min: 0
                max: 1
        
        BoxLayout:
            padding: "10dp"
            orientation: "horizontal"    
            MDLabel:
                id: status
                text:"--"
                       
        MDRectangleFlatButton:
            text:"Flash"
            pos_hint:{'center_x': .5, 'center_y': .5}
            on_release:app.on_flash()
'''


class MainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ih = IntelHex()
        self.ab = ArduinoBootloader()
        self.working_thread = None
        self.progress_queue = Queue(100)

    def build(self):
        return Builder.load_string(KV)

    def on_flash(self):
        self.ih.fromfile('test.hex', format='hex')

        self.root.ids.file_info.text = "start {} end {}".format(self.ih.minaddr(), self.ih.maxaddr())

        self.root.ids.progress.value = 0
        self.working_thread = threading.Thread(target=self.thread_flash)
        self.working_thread.start()

    def thread_flash(self):
        res_val = False

        if self.ab.open():
            if self.ab.board_request():
                self.progress_queue.put(["board_request"])
                Clock.schedule_once(self.progress_callback, 1 / 1000)

            if self.ab.cpu_signature():
                self.progress_queue.put(["cpu_signature"])
                Clock.schedule_once(self.progress_callback, 1 / 1000)

            for address in range(0, self.ih.maxaddr(), self.ab.cpu_page_size*2):
                buffer = self.ih.tobinarray(start=address, size=self.ab.cpu_page_size*2)
                res_val = self.ab.write_memory(buffer, int(address/2))
                if not res_val:
                    break

                self.progress_queue.put(["write", address / self.ih.maxaddr()])
                Clock.schedule_once(self.progress_callback, 1 / 1000)

            if res_val:
                for address in range(0, self.ih.maxaddr(), self.ab.cpu_page_size * 2):
                    buffer = self.ih.tobinarray(start=address, size=self.ab.cpu_page_size * 2)
                    read_buffer = self.ab.read_memory(int(address / 2), self.ab.cpu_page_size * 2)
                    if not len(read_buffer) or (buffer != read_buffer):
                        res_val = False
                        break

                    self.progress_queue.put(["read", address / self.ih.maxaddr()])
                    Clock.schedule_once(self.progress_callback, 1 / 1000)

            self.progress_queue.put(["result", "ok" if res_val else "error", address])
            Clock.schedule_once(self.progress_callback, 1 / 1000)

        self.ab.close()

    def progress_callback(self, dt):
        value = self.progress_queue.get()

        if value[0] == "board_request":
            self.root.ids.sw_version.text = self.ab.sw_version
            self.root.ids.hw_version.text = self.ab.hw_version

        if value[0] == "cpu_signature":
            self.root.ids.cpu_version.text = self.ab.cpu_name

        if value[0] == "write":
            self.root.ids.status.text = "Writing Flash %{:.2f}".format(value[1]*100)
            self.root.ids.progress.value = value[1]

        if value[0] == "read":
            self.root.ids.status.text = "Reading Flash %{:.2f}".format(value[1]*100)
            self.root.ids.progress.value = value[1]

        if value[0] == "result" and value[1] == "ok":
            self.root.ids.status.text = "Writing Flash %100.00"
            self.root.ids.progress.value = 1

        if value[0] == "result" and value[1] == "error":
            self.root.ids.status.text = "Error writing"


MainApp().run()
