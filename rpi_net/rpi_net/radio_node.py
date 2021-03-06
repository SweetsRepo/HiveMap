import asyncio
import json

from random import randint

import serial
from serial.tools import list_ports

class RadioNode():
    """
    Node handing Communication to the A-Layer via serial connection
    """
    def __init__(self, main_server):
        self.main_server = main_server
        self.json_map = {
            "c" : "occupied",
            "n" : "quiet"
        }
        self.connect_serial()

    def connect_serial(self):
        '''
        Attempts to make a serial connection to an arduino with a radio comm unit
        '''
        ports = list(list_ports.comports())
        self.ser = None
        # Searches for Arduino name on Windows Systems
        for p in ports:
            if "Arduino" in p.description:
                self.ser = serial.Serial(p.device, 9600)
                break
        # Probably not connected or it's running a real OS
        if self.ser is None:
            if ports:
                self.ser = serial.Serial(ports[0].device, 9600)

    async def run(self):
        """
        Task which collects updates from the serial link and triggers updates
        to a single room's state. This in turn triggers Pi-Layer Syncronization
        """
        while True:
            await asyncio.sleep(0)

            if self.ser is not None:
                line = self.ser.readline()
                # Creates an update to the state if room update has a valid format
                try:
                    room_update = json.loads(line)
                    room_id = f"Room {room_update['r']}"
                    floor_name = self.main_server.config["floors"][0]["name"]
                    # Build out the state update
                    state = {
                        room_id: {
                            "dynamic_props": {}
                        }
                    }

                    for key in self.json_map:
                        if key in room_update:
                            state[room_id]["dynamic_props"][self.json_map[key]] = room_update[key]
                    await self.main_server.set_room_state("Floor 1", state)
                except (AttributeError, KeyError, UnicodeDecodeError, json.decoder.JSONDecodeError) as e:
                    pass


    async def run_stubbed(self):
        """
        Task alternative to actual hardware updates from the A-Layer
        """
        while True:
            await asyncio.sleep(0)
            # Randomly selects a floor and then a room on that floor to change the state of
            # Seems messy, but this flow would never normally exist beyond demos
            floor_select = randint(1, len(self.main_server.config["floors"])-1)
            floor_name = self.main_server.config["floors"][floor_select]["name"]
            max_room = 0
            for room in self.main_server.config["rooms"]:
                if room["static_props"]["loc"]["floor"] == floor_name:
                    max_room += 1
            fakeState = {
                f"Room {randint(1, max_room)}": {
                    "dynamic_props":{
                        "occupied": randint(0,1),
                        "quiet": randint(0,1)

                    }
                }
            }
            await self.main_server.set_room_state(floor_name, fakeState)
