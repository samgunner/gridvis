# Sam Gunner 230920
# This script will recieve the grid intensity signals broadcast over the Twinergy NATS
# server and then display them on the Blinkt! LEDs.
# The right most LED will be current condition of the grid, with the LEDs to the left of
# that displaying a history. Each LED will represent a differen 15 minute slot.
# we're going to try and use a Queue...

import asyncio
import nats
import time
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

import blinkt
import json
from queue import Queue

# a few global variables

# A brightness variable, 1 is full, 0 is off.
brightness = 0.5

# the number of steps there in the LED pulsing:
pulse_steps = 25
# TODO, brightness is not linear, so it would be good to implement something that takes account of that.

# the delay pulsing sleep timer. the lower the number, the faster the pulsing.
pulse_wait = 1/400

# the queue we are going to try and use to get data between the nats subcribe functionalist and the 
# blikt! management stuff.
q = Queue()

# the function that will hopefully recieve the messages on teh nats broker
async def nat_sub():
    # It is very likely that the demo server will see traffic from clients other than yours.
    # To avoid this, start your own locally and modify the example to use it.

    # Connect to NATS!
    nc = nats.NATS()
    await nc.connect(servers="nats://natstwinergy.etra-id.com:4223",
                     token="uBCdpRHUhuQsc4Q8Po",
                     max_reconnect_attempts=1)

    # Receive messages on 'foo'
    sub = await nc.subscribe("M5.data.energylight.bristol")

    # Publish a message to 'foo'
    # await nc.publish("foo", b'Hello from Python!')
    while 1:
        # Process a message
        try:
            msg = await sub.next_msg()
            print("Received:", msg)
            data = json.loads(msg.data)

            # send it to the queue so that it can eb displayed by the blinkt
            q.put(data['energy_light'])

        except Exception as e:
            print(e)
        await asyncio.sleep(60)


    # Close NATS connection
    await nc.close()

# the function that will hopefully update the blinkt LEDs.
async def display_LEDS():

    # the list that will contain the historic value.
    signal_history = list()
    # a test starting history, so that we don't have to wait forever...
    #signal_history = list(('red','green', 'yellow', 'green', 'yellow', 'red', 'green', 'yellow'))

    # a variable that will be counted through to make the left most LED flash
    t = 0
    
    # and a variable say if the flashing is going up or down, 1 is up, -1 is down.
    upordown = 1

    while True:
        # check to see if there is anything in the queue
        while not q.empty():
            message = q.get()
            if message is None: 
                continue
            # and if there is then update the signal history
            signal_history = list((message, *signal_history[:(blinkt.NUM_PIXELS-1)]))
        
        if signal_history:
            # set the plusing on the LED 0, 
            blinkt.set_pixel(0, *[int(i*(t/pulse_steps)) 
                for i in wordToRGB(signal_history[0])])
    
            # either increment or decrement the pulse brightness value.
            if upordown > 0:
                t = t + 1
                if (t >= pulse_steps):
                    upordown = -1
            else:
                t = t - 1
                if (t <= 0):
                    upordown = 1
    
            # now for the other LED go through the history and update accordingly
            for i in range(1,len(signal_history)):
                blinkt.set_pixel(i, *wordToRGB(signal_history[i]))
    
            blinkt.show()
    
        await asyncio.sleep(pulse_wait)

# a function that will convert the 'red', 'yellow', 'green' into rgb
def wordToRGB(colour):
    if colour == 'red':
        return (int(255*brightness), 0, 0)
    elif colour == 'yellow':
        return (int(255*brightness), int(191*brightness), 0)
    elif colour == 'green':
        return (0, int(255*brightness), 0)
    else:
        print('Error - unknown colour: {}'.format(colour))
        return (int(255*brightness), 0, int(255*brightness))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(nat_sub(), display_LEDS()))
    loop.close()

