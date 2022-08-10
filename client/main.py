#!/usr/bin/env python3
# Author: Gary Kim

import aioesphomeapi
import asyncio
import threading
import time
import boto3
import math

# BEGIN: From user4815162342 on Stack Overflow

def _start_async():
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever).start()
    return loop

_loop = _start_async()

# Submits awaitable to the event loop, but *doesn't* wait for it to
# complete. Returns a concurrent.futures.Future which *may* be used to
# wait for and retrieve the result (or exception, if one was raised)

def submit_async(awaitable):
    return asyncio.run_coroutine_threadsafe(awaitable, _loop)

def stop_async():
    _loop.call_soon_threadsafe(_loop.stop)


api = aioesphomeapi.APIClient("sinkmate.local", 6053, "sinkmate")
api_info = {
    'connected': False,
    'safety_ping_key': 0,
}

state = {}

async def _init():
    """Connect to an ESPHome device and get details."""
    
    print("Logging in...")

    # Establish connection
    await api.connect(login=True)
    api_info['connected'] = True

    # Get API version of the device's firmware
    # print(api.api_version)

    # Show device details
    device_info = await api.device_info()
    print("Board connected!")

    # List all entities of the device
    entities = (await api.list_entities_services())[0]
    for entity in entities:
        state[str(entity.key)] = {
            'name': entity.name,
            'id': entity.object_id,
            'value': 0,
        }
        if entity.object_id == "safety_ping":
            api_info['safety_ping_key'] = entity.key

    def cb_save_state(s):
        state[str(s.key)]['value'] = s.state

    await api.subscribe_states(cb_save_state)

def switch(cmd):
    for key, dev in state.items():
        if not dev['id'] == cmd[1]:
            continue
        # print("Setting", dev['name'], 'with key', key, "to", cmd[2] == "True" or cmd[2] == "on")
        asyncio.run(api.switch_command(int(key), cmd[2] == "True" or cmd[2] == "on"))

def run(cmd):
    if cmd[0] == "list" and len(cmd) == 1:
        print(state)
        return
    if cmd[0] == "set" and len(cmd) == 3:
        switch(cmd)
        return
    if cmd[0] == "get" and len(cmd) == 2:
        for key, dev in state.items():
            if not dev['id'] == cmd[1]:
                return
            print(dev['value'])
            return
        return
    print("INVALID COMMAND!")

# SQS Setup
f = open("keys.txt", "r")
keys = f.read().split(",")
sqs = boto3.resource('sqs', region_name="us-east-1", aws_secret_access_key=str(keys[0]), aws_access_key_id=str(keys[1]))
queue = sqs.get_queue_by_name(QueueName = 'dispense-queue')

# Dictionary setup from file

print("Reading file...")
f = open("presets.txt", "r")
entries = f.read().split(";")
entries.pop(len(entries)-1)
name_dict = dict()
for arr in entries:
    parts = arr.split(",")
    name_dict[parts[0]] = [parts[1], parts[2]]
print("Dictionary initialized.")
f.close()

# Main Loop

def main():
    time.sleep(3)
    
    sensor_key = "940400599"
    total_key = "1402521437"
    valve_key = "636313445"
    while True:

        # Checks for queue message

        for msg in queue.receive_messages(MessageAttributeNames=['Name', 'Amount', 'Unit']):

            # Obtain message from queue

            attr = msg.message_attributes
            amt = attr["Amount"]["StringValue"]
            unit = attr["Unit"]["StringValue"]
            name = attr["Name"]["StringValue"]
            print('-------------------QUEUE RECEIVE-------------------------')
            print("Body: "+msg.body+"\tName: "+name+"\tAmount: " + amt + "\tUnit: " + unit)
            print('---------------------------------------------------------')
            msg.delete()

            # Passthrough mode implementation

            if msg.body == "PassOn":
                run(("set valve "+str(True)).split(" "))
                continue
            elif msg.body == "PassOff":
                run(("set valve "+str(False)).split(" "))
                continue

            # Preset implementation

            elif msg.body == "Preset":
                f = open("presets.txt", "a")
                f.write(name+","+amt+","+unit+";")
                name_dict[name] = [amt, unit]
                print("Updated presets.")
                f.close()
                continue
            
            # Dispensing implementation

            elif msg.body == "Dispense":

                # Has a preset

                if name != "none":
                    amt = name_dict[name][0]
                    unit = name_dict[name][1]
                    print("Dispensing using preset \"" + name+"\" with "+amt+" "+unit+".")

                # Does not have a preset
                
                else:
                    print("Dispensing using measurements.")

                # Unit conversion to milliliters

                amt = float(amt)
                if unit == "gallon":
                    amt*=3785.41
                elif unit == "quart":
                    amt*=946.353
                elif unit == "pint": 
                    amt*=473.176 
                elif unit == "fluid ounce":
                    amt*=29.574
                elif unit == "cup":
                    amt*=240
                elif unit == "liter":
                    amt*=1000
                elif unit == "tablespoon":
                    amt*=14.787
                unit = "milliliter"

                run(("set valve "+str(True)).split(" "))
                required_pulses = math.floor(amt/2.25)
                print("Pulses required: " + str(required_pulses))
                elapsed_pulses = 0
                while elapsed_pulses <= required_pulses:
                    elapsed_pulses = state[total_key]['value']

                print("Dispense complete! Pulses elapsed: " + str(elapsed_pulses))
                run(("set valve "+str(False)).split(" "))
                    

submit_async(_init())
main()