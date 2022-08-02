#!/usr/bin/env python3
# Author: Gary Kim

import aioesphomeapi
import asyncio
import threading
import time
import boto3

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

state = {}
api = aioesphomeapi.APIClient("sinkmate.local", 6053, "sinkmate")
api_info = {
    'connected': False,
    'safety_ping_key': 0,
}

savefile = open('./save.csv', 'w')
begintime = time.time()

async def _init():
    """Connect to an ESPHome device and get details."""

    # Establish connection
    # api = aioesphomeapi.APIClient("cooper-hyperloop-brake-dyno.local", 6053, "")
    await api.connect(login=True)
    api_info['connected'] = True

    # Get API version of the device's firmware
    print(api.api_version)

    # Show device details
    device_info = await api.device_info()
    print(device_info)

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
        print("Setting", dev['name'], 'with key', key, "to", cmd[2] == "True" or cmd[2] == "on")
        asyncio.run(api.switch_command(int(key), cmd[2] == "True" or cmd[2] == "on"))

# SQS Setup

sqs = boto3.resource('sqs', region_name="us-east-1", aws_secret_access_key="PRIVATE", aws_access_key_id="PRIVATE")
queue = sqs.get_queue_by_name(QueueName = 'dispense-queue')

# Main Loop

def main():
    while True:

        # Pulls queue message

        amt = 0
        unit = ""
        for msg in queue.receive_messages(MessageAttributeNames=['Amount', 'Unit']):
            attr = msg.message_attributes
            amt = int(attr["Amount"]["StringValue"])*2
            unit = attr["Unit"]["StringValue"]
            print("Amount: " + str(amt) + "\tUnit: " + unit)
            # Let the queue know that the message is processed
            msg.delete()
        
        current = False
        while amt > 0:
            time.sleep(1)
            current = not current
            cmd = ("set led " + str(current)).split(" ")
            if cmd[0] == "list" and len(cmd) == 1:
                print(state)
                continue
            if cmd[0] == "set" and len(cmd) == 3:
                switch(cmd)
                amt-=1
                continue
            if cmd[0] == "get" and len(cmd) == 2:
                for key, dev in state.items():
                    if not dev['id'] == cmd[1]:
                        continue
                    print(dev['value'])
                    break
                continue
            if cmd[0] == "auto" and len(cmd) == 2:
                switch(["set", "motor", "on"])
                time.sleep(float(cmd[1]))
                switch(["set", "brake", "on"])
                continue
            if cmd[0] == "exit":
                savefile.flush()
                savefile.close()
                exit()
            if cmd[0] == "save":
                savefile.flush()
                continue
            print("INVALID COMMAND!")

submit_async(_init())
main()
