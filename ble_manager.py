import asyncio
import sys
from bleak import BleakClient
import pandas as pd
from datetime import datetime

class BleDevice:
    def __init__(self, address, service_uuid, tx_char_uuid, rx_char_uuid):
        self.address = address
        self.service_uuid = service_uuid
        self.tx_char_uuid = tx_char_uuid
        self.rx_char_uuid = rx_char_uuid
        self.client = None
        self.received_data = ""

    def notification_handler(self, sender, data):
        self.received_data = data.decode()

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

    async def get_measurement(self):
        await self.connect()
        await self.send_command("new_measure")
        #await asyncio.sleep(0.1)  # Wait for the data to be received
        await self.disconnect()
        return self.received_data

async def main():
    DEVICE_ADDRESS = "28:CD:C1:0F:8F:03"
    SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    TX_CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
    RX_CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

    ble_device = BleDevice(DEVICE_ADDRESS, SERVICE_UUID, TX_CHARACTERISTIC_UUID, RX_CHARACTERISTIC_UUID)
    data = await ble_device.get_measurement()

    if data:
        cleaned_data = data.strip("()").split(", ")
        systolic_pressure  = int(cleaned_data[0])
        diastolic_pressure = int(cleaned_data[1])

        new_measurement = {
            'Date_of_Measurement': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Systolic_Pressure': systolic_pressure,
            'Diastolic_Pressure': diastolic_pressure,
        }

        df = pd.DataFrame([new_measurement])
        df.to_csv("result_measurement.csv", index=False)

if __name__ == "__main__":
    asyncio.run(main())
