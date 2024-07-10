import asyncio
from bleak import BleakClient
import re

class BleDevice:
    def __init__(self, address, service_uuid, tx_char_uuid, rx_char_uuid):
        self.address = address
        self.service_uuid = service_uuid
        self.tx_char_uuid = tx_char_uuid
        self.rx_char_uuid = rx_char_uuid
        self.client = None
        self.data_received = []

    def notification_handler(self, sender, data):
        self.data_received.append(data.decode())
        print(f"Received chunk: {data.decode()}")

    async def connect(self):
        self.client = BleakClient(self.address)
        await self.client.connect()
        connected = self.client.is_connected
        print(f"Connected: {connected}")
        if connected:
            await self.client.start_notify(self.tx_char_uuid, self.notification_handler)

    async def disconnect(self):
        if self.client:
            await self.client.stop_notify(self.tx_char_uuid)
            await self.client.disconnect()
            print("Disconnected")

    async def send_command(self, command):
        if self.client:
            await self.client.write_gatt_char(self.rx_char_uuid, command.encode())
            print(f"Command sent: {command}")

    async def get_measurement(self, timeout=10):
        await self.connect()
        await self.send_command("request_measures")
        
        # Wait for data until the timeout is reached
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            await asyncio.sleep(0.1)  # Wait for data to be received

        await self.disconnect()
        return self.data_received



def clean_and_format_data(data_chunks):
    # Join all data chunks into a single string
    full_data = ''.join(data_chunks)
    
    # Use a regular expression to find all occurrences of the pattern
    pattern = re.compile(r"\(([^)]+)\)")
    matches = pattern.findall(full_data)
    
    formatted_lines = []
    for match in matches:
        # Split the match into timestamp and values
        timestamp, values = match.split(", [")
        values = values.rstrip("]")
        
        # Format and append the result
        formatted_lines.append(f"({timestamp}, [{values}])")
    
    return formatted_lines

async def main():
    DEVICE_ADDRESS = "28:CD:C1:0F:8F:03"
    SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    TX_CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
    RX_CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

    ble_device = BleDevice(DEVICE_ADDRESS, SERVICE_UUID, TX_CHARACTERISTIC_UUID, RX_CHARACTERISTIC_UUID)
    data_received = await ble_device.get_measurement()

    if data_received:
        formatted_data = clean_and_format_data(data_received)
        with open("requested_measures.txt", "a") as file:
            for line in formatted_data:
                file.write(line + "\n")

if __name__ == "__main__":
    asyncio.run(main())