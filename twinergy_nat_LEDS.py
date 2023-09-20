import asyncio
import nats
import time
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

import blinkt
import json

async def run():
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

            if data['energy_light'] == 'green':
                blinkt.set_all(0,255,0)
            elif data['energy_light'] == 'yellow':
                blinkt.set_all(255,255,0)
            elif data['energy_light'] == 'red':
                blinkt.set_all(255,0,0)
            else:
                blinkt.set_all(0,0,255)

            blinkt.show()

        except Exception as e:
            print(e)
        time.sleep(60)


    # Close NATS connection
    await nc.close()



if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass

