import sys
import serial
import asyncio
import threading
import serial.tools.list_ports
from bleak import BleakScanner, BleakClient
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

class WAPGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.title("Wildlife Audio Player GUI")
        self.geometry("800x1000")  # Adjusted window size

        # Create main frame
        self.frame = ttk.Frame(self)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        # **Top Section: Bluetooth & UART Selection**
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill="x", pady=20)

        self.connection_type = tk.StringVar()
        self.connection_type.set("UART")  # Default selection

        self.bluetooth_button = ttk.Radiobutton(top_frame, text="Bluetooth", variable=self.connection_type, value="Bluetooth", command=self.uart_button_toggled)
        self.bluetooth_button.pack(side=tk.LEFT, padx=60)

        self.uart_button = ttk.Radiobutton(top_frame, text="UART", variable=self.connection_type, value="UART", command=self.uart_button_toggled)
        self.uart_button.pack(side=tk.RIGHT, padx=100)

        # **Middle Section: Bluetooth Devices & Serial Port**
        middle_frame = ttk.Frame(self.frame)
        middle_frame.pack(fill="x", pady=5)

        # **Bluetooth Side**
        bluetooth_frame = ttk.Frame(middle_frame)
        bluetooth_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=10)

        self.scan_button = ttk.Button(bluetooth_frame, text="Scan for Devices", command=self.start_scan_devices)
        self.scan_button.pack(pady=10)

        # Bluetooth Devices Listbox
        self.devices_label = ttk.Label(bluetooth_frame, text="Discovered Devices:")
        self.devices_label.pack()

        self.devices_listbox = tk.Listbox(bluetooth_frame, height=5)
        self.devices_listbox.pack(pady=5, fill="x")

        # **Bluetooth Connect Button**
        self.bluetooth_connect_button = ttk.Button(bluetooth_frame, text="Connect", command=self.connect_to_bluetooth)
        self.bluetooth_connect_button.pack(pady=5)

        # **UART Side**
        uart_frame = ttk.Frame(middle_frame)
        uart_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=10)

        # **Baud Rate Input**
        baud_frame = ttk.Frame(uart_frame)
        baud_frame.pack(pady=5)

        self.baudrate_label = ttk.Label(baud_frame, text="Baud Rate:")
        self.baudrate_label.pack(side=tk.LEFT, padx=10)

        self.baudrate_var = tk.IntVar(value=9600)  # Default baud rate
        self.baudrate_entry = ttk.Entry(baud_frame, textvariable=self.baudrate_var, width=10)
        self.baudrate_entry.pack(side=tk.LEFT, padx=5)

        # Serial Port Listbox
        self.serial_ports_label = ttk.Label(uart_frame, text="Serial Port:")
        self.serial_ports_label.pack(pady=5)

        self.serial_listbox = tk.Listbox(uart_frame, height=5)
        self.serial_listbox.pack(pady=5, fill="x")

        # **Buttons - Connect and Refresh**
        button_frame = ttk.Frame(uart_frame)
        button_frame.pack(pady=10)

        # **UART Connect Button**
        self.uart_connect_button = ttk.Button(button_frame, text="Connect", command=self.connect_to_uart)
        self.uart_connect_button.pack(side=tk.LEFT, padx=10)

        # **Refresh Button to refresh serial ports**
        self.refresh_button = ttk.Button(button_frame, text="Refresh", command=self.refresh_serial_ports)
        self.refresh_button.pack(side=tk.LEFT, padx=10)

        self.populate_serial_ports()

       # === New Control Section using grid() ===
        control_frame = ttk.LabelFrame(self.frame, text="Controls")
        control_frame.pack(fill="x", pady=10, padx=10)

        # Row 0 - Volume
        ttk.Label(control_frame, text="Volume:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.volume_input = ttk.Entry(control_frame, width=5)
        self.volume_input.grid(row=0, column=1, padx=5, pady=5)
        self.volume_set_button = ttk.Button(control_frame, text="Set", command=self.set_volume)
        self.volume_set_button.grid(row=0, column=2, padx=5, pady=5)

        # # Row 1 - Folder/File (closer together)
        ttk.Label(control_frame, text="Folder #:").grid(row=1, column=0, padx=(5, 2), pady=5, sticky="e")
        self.manual_folder_entry = ttk.Entry(control_frame, width=5)
        self.manual_folder_entry.grid(row=1, column=1, padx=(2, 10), pady=5)

        ttk.Label(control_frame, text="File #:").grid(row=1, column=2, padx=(5, 2), pady=5, sticky="e")
        self.manual_file_entry = ttk.Entry(control_frame, width=5)
        self.manual_file_entry.grid(row=1, column=3, padx=(2, 10), pady=5)

        self.track_send_button = ttk.Button(control_frame, text="Send Track", command=lambda: self.send_folder_file(
            self.manual_folder_entry.get(), self.manual_file_entry.get()))
        self.track_send_button.grid(row=1, column=4, padx=5, pady=5)


        # Row 2 - Duty Cycle
        ttk.Label(control_frame, text="Duty Cycle:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.duty_cycle_input = ttk.Entry(control_frame, width=5)
        self.duty_cycle_input.grid(row=2, column=1, padx=5, pady=5)
        self.duty_cycle_button = ttk.Button(control_frame, text="Set", command=self.set_duty_cycle)
        self.duty_cycle_button.grid(row=2, column=2, padx=5, pady=5)
        # === Scheduler Section ===
        scheduler_frame = ttk.LabelFrame(self.frame, text="Scheduler")
        scheduler_frame.pack(fill="x", pady=10, padx=10)

        # Row 1: Date (Month / Day)
        date_frame = ttk.Frame(scheduler_frame)
        date_frame.pack(pady=5)

        ttk.Label(date_frame, text="Month:").pack(side=tk.LEFT, padx=5)
        self.month_entry = ttk.Entry(date_frame, width=5)
        self.month_entry.pack(side=tk.LEFT)

        ttk.Label(date_frame, text="Date:").pack(side=tk.LEFT, padx=5)
        self.date_entry = ttk.Entry(date_frame, width=5)
        self.date_entry.pack(side=tk.LEFT)
        self.repeat_info_label = ttk.Label(scheduler_frame, text="(Enter Month = 0 for monthly repeating schedules)", foreground="gray")
        self.repeat_info_label.pack(pady=2)

        # Row 2: Start/Stop Time
        time_frame = ttk.Frame(scheduler_frame)
        time_frame.pack(pady=5)

        ttk.Label(time_frame, text="Start (Hr:Min):").pack(side=tk.LEFT, padx=5)
        self.start_hour_entry = ttk.Entry(time_frame, width=3)
        self.start_hour_entry.pack(side=tk.LEFT)
        self.start_min_entry = ttk.Entry(time_frame, width=3)
        self.start_min_entry.pack(side=tk.LEFT)

        ttk.Label(time_frame, text="Stop (Hr:Min):").pack(side=tk.LEFT, padx=5)
        self.stop_hour_entry = ttk.Entry(time_frame, width=3)
        self.stop_hour_entry.pack(side=tk.LEFT)
        self.stop_min_entry = ttk.Entry(time_frame, width=3)
        self.stop_min_entry.pack(side=tk.LEFT)

        # Row 3: Folder # and File #
        file_frame = ttk.Frame(scheduler_frame)
        file_frame.pack(pady=5)

        ttk.Label(file_frame, text="Folder #:").pack(side=tk.LEFT, padx=5)
        self.folder_entry = ttk.Entry(file_frame, width=5)
        self.folder_entry.pack(side=tk.LEFT)

        ttk.Label(file_frame, text="File #:").pack(side=tk.LEFT, padx=5)
        self.file_entry = ttk.Entry(file_frame, width=5)
        self.file_entry.pack(side=tk.LEFT)

        # To add enteries
        self.add_entry_button = ttk.Button(scheduler_frame, text="Add Entry", command=self.add_schedule_entry)
        self.add_entry_button.pack(pady=2)
        # Create a frame to hold both buttons side-by-side
        schedule_button_frame = ttk.Frame(scheduler_frame)
        schedule_button_frame.pack(pady=5)

        # Send Schedules Button
        self.send_all_button = ttk.Button(schedule_button_frame, text="Send Schedules", command=self.send_all_schedules)
        self.send_all_button.pack(side=tk.LEFT, padx=10)

        # Clear Queue Button
        self.clear_queue_button = ttk.Button(schedule_button_frame, text="Clear Queue", command=self.clear_schedule_queue)
        self.clear_queue_button.pack(side=tk.LEFT, padx=10)

        # **Clear and Download Log Button Frame**
        bottom_button_frame = ttk.Frame(self.frame)
        bottom_button_frame.pack(fill="x", padx=10, pady=5)

        # **Download Log Button**
        self.download_log_button = ttk.Button(bottom_button_frame, text="Download Log", command=self.download_log)
        self.download_log_button.pack(side=tk.LEFT, padx=5)

        # **Clear Button**
        self.clear_button = ttk.Button(bottom_button_frame, text="Clear Output", command=self.clear_textbox)
        self.clear_button.pack(side=tk.RIGHT, padx=5)


        # **Devices Text Section (Non-Editable) with Clear Button**
        text_frame = ttk.Frame(self.frame)  # Create a frame to hold the text box and scrollbar
        text_frame.pack(fill="both", padx=5, pady=5)

        # Create a text widget for displaying messages, set as non-editable (DISABLED state)
        self.devices_text = tk.Text(text_frame, height=18, wrap=tk.WORD, state=tk.DISABLED)
        self.devices_text.pack(side=tk.LEFT, fill="both", expand=True)

        # Add a scrollbar to the text widget
        scrollbar = ttk.Scrollbar(text_frame, command=self.devices_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.devices_text.config(yscrollcommand=scrollbar.set)  # Link the scrollbar to the text widget

        # Initialize connections
        self.uart_button_toggled() # Call uart_button_toggled to adjust the state based on the initial connection type
        self.serial_conn = None
        self.ble_device = None
        self.ble_client = None
        self.ble_characteristic_uuid = "YOUR-CHARACTERISTIC-UUID-HERE"  # <- Change this to device UUID
        self.device_connected = False  # Track device connection status
        self.schedule_entries = []  # To track existing scheduled intervals
        self.schedule_queue = []
        self.is_scanning = False
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.scan_timeout = 2  # Scan timeout in seconds
        self.debug_mode = True  # Debug messages
        self.after(200, self.poll_uart_data)


    def devices_text_insert(self, text, debug=False):
        """Insert text into the text box. If debug=True, only show if debug_mode is enabled."""
        if debug and not self.debug_mode:
            return  # Skip debug output unless debug_mode is on

        self.devices_text.config(state=tk.NORMAL)
        self.devices_text.insert(tk.END, text + "\n")
        self.devices_text.config(state=tk.DISABLED)
        self.devices_text.yview(tk.END)


    def clear_textbox(self):
        """Clear the devices text display."""
        self.devices_text.config(state=tk.NORMAL)  # Enable editing temporarily
        self.devices_text.delete("1.0", tk.END)  # Delete all text from the widget
        self.devices_text.config(state=tk.DISABLED)  # Disable editing again

    
    # Modify the connect_to_device method to include checks based on connection type
    def connect_to_device(self):
        """Connect using Bluetooth or UART with checks for valid configuration."""
        if self.connection_type.get() == "Bluetooth":
            self.connect_to_bluetooth()
        elif self.connection_type.get() == "UART":
            if self.baudrate_var.get() and self.serial_listbox.curselection():
                self.connect_to_uart()
            else:
                self.devices_text_insert("Error: UART requires both baudrate and serial port.")
        else:
            self.devices_text_insert("Error: Invalid connection type selected.")

    # Modify the start_scan_devices method to ensure Bluetooth is selected when scanning for devices
    def start_scan_devices(self):
        if self.connection_type.get() == "Bluetooth":
            if not self.is_scanning:
                self.devices_text_insert("[BT] Starting Bluetooth scan...", debug=True)
                self.is_scanning = True
                threading.Thread(target=self.run_asyncio_loop).start()
        else:
            self.devices_text_insert("Error: Bluetooth not selected as desired connection method.")

    def run_asyncio_loop(self):
        self.devices_text_insert("[ASYNC] Starting asyncio loop for Bluetooth scan", debug=True)
        asyncio.run(self.scan_devices_async())

    async def scan_devices_async(self):
        try:
            devices = await BleakScanner.discover(timeout=self.scan_timeout)
            self.devices_listbox.delete(0, tk.END)
            for device in devices:
                self.devices_text_insert(f"[BT] Found device: {device.name}", debug=True)
                self.devices_listbox.insert(tk.END, device.name)
            self.devices_text_insert("[BT] Scan complete", debug=True)
        except Exception as e:
            self.devices_text_insert(f"[BT][ERROR] Bluetooth scan failed: {e}")
        finally:
            self.is_scanning = False

    async def async_connect_to_bluetooth(self, device_name):
        """Asynchronous Bluetooth connection logic."""
        try:
            devices = await BleakScanner.discover(timeout=self.scan_timeout)
            for device in devices:
                if device.name == device_name:
                    self.ble_device = device
                    self.ble_client = BleakClient(device)

                    await self.ble_client.connect()
                    if self.ble_client.is_connected:
                        self.device_connected = True
                        self.devices_text_insert(f"[BT] Connected successfully to {device_name}.", debug=True)
                    else:
                        self.devices_text_insert(f"[BT][ERROR] Failed to connect to {device_name}.")
                    return
            self.devices_text_insert(f"[BT][ERROR] Device '{device_name}' not found during scan.")
        except Exception as e:
            self.devices_text_insert(f"[BT][ERROR] during connection: {str(e)}", debug=True)

    def connect_to_bluetooth(self):
        """Connect to Bluetooth device asynchronously."""
        if self.connection_type.get() == "Bluetooth":
            selection = self.devices_listbox.curselection()
            if not selection:
                self.devices_text_insert("[BT][ERROR] No Bluetooth device selected.")
                return

            index = selection[0]
            selected_device_name = self.devices_listbox.get(index)
            self.devices_text_insert(f"[BT] Attempting to connect to {selected_device_name}...", debug=True)

            threading.Thread(
                target=lambda: asyncio.run(self.async_connect_to_bluetooth(selected_device_name))
            ).start()

    #Wrapper for non-async context
    def send_over_bluetooth(self, data_bytes):
        """Send bytes over Bluetooth in a new thread."""
        if not self.device_connected:
            self.devices_text_insert("[BT][ERROR] Cannot send, no device connected.")
            return

        self.devices_text_insert(f"[BT][TX] Sending data: {list(data_bytes)}", debug=True)

        threading.Thread(
            target=lambda: asyncio.run(self.bluetooth_send(data_bytes))
        ).start()
    
    async def bluetooth_send(self, data_bytes):
        """Actual asynchronous sending over BLE."""
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.write_gatt_char(self.ble_characteristic_uuid, data_bytes)
                self.devices_text_insert(f"[BT][TX] Write success.", debug=True)
            except Exception as e:
                self.devices_text_insert(f"[BT][ERROR] Failed to write data: {e}")
        else:
            self.devices_text_insert("[BT][ERROR] BLE client not connected.")




    # Add logic to ensure only one connection controls are avilble at one time
    def uart_button_toggled(self):
        """Toggle widgets based on UART or Bluetooth selection."""
        if self.connection_type.get() == "UART":
            self.baudrate_entry.config(state=tk.NORMAL)
            self.serial_listbox.config(state=tk.NORMAL)
            self.uart_connect_button.config(state=tk.NORMAL)
            self.refresh_button.config(state=tk.NORMAL)

            # Disable Bluetooth widgets
            self.devices_listbox.config(state=tk.DISABLED)
            self.bluetooth_connect_button.config(state=tk.DISABLED)
            self.scan_button.config(state=tk.DISABLED)

        else:
            self.baudrate_entry.config(state=tk.DISABLED)
            self.serial_listbox.config(state=tk.DISABLED)
            self.uart_connect_button.config(state=tk.DISABLED)
            self.refresh_button.config(state=tk.DISABLED)

            # Enable Bluetooth widgets
            self.devices_listbox.config(state=tk.NORMAL)
            self.bluetooth_connect_button.config(state=tk.NORMAL)
            self.scan_button.config(state=tk.NORMAL)


    def populate_serial_ports(self):
        """Populate the available serial ports."""
        self.serial_ports = list(serial.tools.list_ports.comports())
        self.serial_listbox.delete(0, tk.END)
        for port in self.serial_ports:
            self.serial_listbox.insert(tk.END, port.device)

    # Modify the refresh_serial_ports method to ensure UART is selected before refreshing
    def refresh_serial_ports(self):
        """Refresh the list of available serial ports."""
        if self.connection_type.get() == "UART":
            self.populate_serial_ports()
        else:
            self.devices_text_insert("Error: UART must be selected to refresh serial ports.")

    def connect_to_uart(self):
        if self.connection_type.get() == "UART":
            try:
                selection = self.serial_listbox.curselection()
                if not selection:
                    self.devices_text_insert("Error: No UART port selected.")
                    return

                index = selection[0]
                selected_port = self.serial_listbox.get(index)
                baudrate = self.baudrate_var.get()

                self.devices_text_insert(f"[UART] Attempting to connect to {selected_port} at {baudrate}...", debug=True)
                self.serial_conn = serial.Serial(selected_port, baudrate, timeout=1)
                self.device_connected = True
                self.devices_text_insert(f"Connected to UART on {selected_port} at {baudrate} baud.")

                # Start continuous UART polling
                self.poll_uart_data()

            except Exception as e:
                self.devices_text_insert(f"[UART][ERROR] {str(e)}", debug=True)
        else:
            self.devices_text_insert("Error: UART not selected as desired connection method.")


    def ensure_device_connected(self):
        """Check if a device is connected before executing commands."""
        if not self.device_connected:
            self.devices_text_insert("Error: No device connected. Connect via Bluetooth or UART first.")
            return False
        return True
    
    def poll_uart_data(self):
        """Continuously check for UART data and display it."""
        if self.serial_conn and self.serial_conn.in_waiting:
            try:
                data = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
                if data:
                    self.devices_text_insert(f"[UART][RX] {data}", debug=True)
            except Exception as e:
                self.devices_text_insert(f"[UART][ERROR] {e}", debug=True)
        
        # Schedule to check again after 200ms
        self.after(200, self.poll_uart_data)


    def set_volume(self):
        """Set the system volume (0-100%) and send command over UART or Bluetooth."""
        if not self.ensure_device_connected():
            return  # No device connected, skip

        try:
            volume = int(self.volume_input.get())

            # Validate volume range
            if 0 <= volume <= 100:
                self.devices_text_insert(f"Volume set to: {volume}%")

                if self.connection_type.get() == "UART" and self.serial_conn:
                    # UART Transmission
                    self.devices_text_insert(f"[UART][TX] Sending volume command: 0x00 {volume}", debug=True)
                    self.serial_conn.write(bytes([0x00, volume]))

                elif self.connection_type.get() == "Bluetooth" and self.device_connected:
                    # Bluetooth Transmission
                    self.devices_text_insert(f"[BT][TX] Sending volume command: 0x00 {volume}", debug=True)
                    self.send_over_bluetooth(bytes([0x00, volume]))

                else:
                    self.devices_text_insert("Error: No valid connection.")

            else:
                # Volume out of valid 0–100 range
                self.devices_text_insert("Error: Volume must be between 0 and 100.")

        except ValueError:
            # Non-integer input
            self.devices_text_insert("Error: Please enter a valid number for volume.")


    def send_folder_file(self, folder, file):
        """Send a specific folder and file selection command to the device over UART or Bluetooth."""
        if not self.ensure_device_connected():
            return  # No device connected, skip

        try:
            folder = int(folder)
            file = int(file)

            # Validate folder and file numbers
            if 0 <= folder <= 255 and 0 <= file <= 255:
                self.devices_text_insert(f"Sending Folder #{folder}, File #{file}")

                if self.connection_type.get() == "UART" and self.serial_conn:
                    # UART Transmission
                    self.devices_text_insert(f"[UART][TX] Sending folder/file command: 0x01 {folder} {file}", debug=True)
                    self.serial_conn.write(bytes([0x01, folder, file]))

                elif self.connection_type.get() == "Bluetooth" and self.device_connected:
                    # Bluetooth Transmission
                    self.devices_text_insert(f"[BT][TX] Sending folder/file command: 0x01 {folder} {file}", debug=True)
                    self.send_over_bluetooth(bytes([0x01, folder, file]))

                else:
                    self.devices_text_insert("Error: No valid connection.")

            else:
                # Folder or file out of valid 0–255 range
                self.devices_text_insert("Error: Folder and File must be between 0 and 255.")

        except ValueError:
            # Non-integer inputs
            self.devices_text_insert("Error: Invalid folder or file number. Please enter valid integers.")



    def set_duty_cycle(self):
        """Set the system duty cycle (0-100%) and send command over UART or Bluetooth."""
        if not self.ensure_device_connected():
            return  # No device connected, skip further actions

        try:
            duty_cycle = int(self.duty_cycle_input.get())

            # Check if duty cycle is in valid range
            if 0 <= duty_cycle <= 100:
                self.devices_text_insert(f"Duty cycle set to: {duty_cycle}%")

                if self.connection_type.get() == "UART" and self.serial_conn:
                    # UART Transmission
                    self.devices_text_insert(f"[UART][TX] Sending duty cycle command: 0x04 {duty_cycle}", debug=True)
                    self.serial_conn.write(bytes([0x04, duty_cycle]))

                elif self.connection_type.get() == "Bluetooth" and self.device_connected:
                    # Bluetooth Transmission
                    self.devices_text_insert(f"[BT][TX] Sending duty cycle command: 0x04 {duty_cycle}", debug=True)
                    self.send_over_bluetooth(bytes([0x04, duty_cycle]))

                else:
                    self.devices_text_insert("Error: No valid connection.")

            else:
                # Duty cycle value out of range
                self.devices_text_insert("Error: Duty cycle must be between 0 and 100.")

        except ValueError:
            # Non-integer input
            self.devices_text_insert("Error: Please enter a valid number for duty cycle.")


    def download_log(self):
        """Request and download system log from the device (UART or Bluetooth)."""
        if not self.ensure_device_connected():
            self.devices_text_insert("Error: No device connected.")
            return

        self.devices_text_insert("Requesting log download...")

        if self.connection_type.get() == "UART" and self.serial_conn:
            try:
                # UART Download Logic
                self.devices_text_insert("[UART][TX] Sending log request command: 0x02", debug=True)
                self.serial_conn.write(bytes([0x02]))

                high = self.serial_conn.read(1)
                low = self.serial_conn.read(1)

                if not high or not low:
                    self.devices_text_insert("[UART][ERROR] Failed to receive log size.")
                    return

                size = (high[0] << 8) | low[0]
                self.devices_text_insert(f"[UART][RX] Log size received: {size} bytes", debug=True)

                received_data = b""
                while len(received_data) < size:
                    chunk = self.serial_conn.read(size - len(received_data))
                    if not chunk:
                        break
                    received_data += chunk
                    self.devices_text_insert(f"[UART][RX] Received {len(received_data)} / {size} bytes...", debug=True)

                log_text = received_data.decode(errors="replace")
                self.preview_and_save_log(log_text)

            except Exception as e:
                self.devices_text_insert(f"[UART][ERROR] during log download: {e}", debug=True)

        elif self.connection_type.get() == "Bluetooth" and self.device_connected:
            try:
                # Bluetooth Download Logic
                self.devices_text_insert("[BT][TX] Sending log request command: 0x02", debug=True)
                self.send_over_bluetooth(bytes([0x02]))

                # Wait for device to send size (2 bytes) over BLE
                async def ble_download():
                    if self.ble_client and self.ble_client.is_connected:
                        high = await self.ble_client.read_gatt_char(self.ble_characteristic_uuid)
                        low = await self.ble_client.read_gatt_char(self.ble_characteristic_uuid)

                        if not high or not low:
                            self.devices_text_insert("[BT][ERROR] Failed to receive log size.")
                            return

                        size = (high[0] << 8) | low[0]
                        self.devices_text_insert(f"[BT][RX] Log size received: {size} bytes", debug=True)

                        received_data = b""
                        while len(received_data) < size:
                            chunk = await self.ble_client.read_gatt_char(self.ble_characteristic_uuid)
                            if not chunk:
                                break
                            received_data += chunk
                            self.devices_text_insert(f"[BT][RX] Received {len(received_data)} / {size} bytes...", debug=True)

                        log_text = received_data.decode(errors="replace")
                        self.preview_and_save_log(log_text)
                    else:
                        self.devices_text_insert("[BT][ERROR] No BLE connection active.")

                threading.Thread(target=lambda: asyncio.run(ble_download())).start()

            except Exception as e:
                self.devices_text_insert(f"[BT][ERROR] during log download: {e}", debug=True)

        else:
            self.devices_text_insert("Error: Log download only supported over UART or Bluetooth.")



    #Helper function for preview and save log
    def preview_and_save_log(self, log_text):
        """Helper to preview and save downloaded log."""
        preview = log_text[:300] + ("..." if len(log_text) > 300 else "")
        self.devices_text_insert("Log Preview:\n" + preview)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"log_{timestamp}.txt"

        file_path = filedialog.asksaveasfilename(
            title="Save Log As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            initialfile=default_filename
        )

        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(log_text)
            self.devices_text_insert(f"Log saved to {file_path}")
        else:
            self.devices_text_insert("Save canceled by user.")


    def add_schedule_entry(self):
        """Validate and add a schedule entry to the queue (but don't send it)."""
        try:
            month = int(self.month_entry.get())
            date = int(self.date_entry.get())
            start_hour = int(self.start_hour_entry.get())
            start_min = int(self.start_min_entry.get())
            stop_hour = int(self.stop_hour_entry.get())
            stop_min = int(self.stop_min_entry.get())
            folder = int(self.folder_entry.get())
            file = int(self.file_entry.get())

            valid_minutes = [0, 15, 30, 45]
            if start_min not in valid_minutes or stop_min not in valid_minutes:
                self.devices_text_insert("Error: Minutes must be 00, 15, 30, or 45.")
                return

            if (stop_hour, stop_min) <= (start_hour, start_min):
                self.devices_text_insert("Error: Stop time must be after start time.")
                return

            # Check for overlap
            for entry in self.schedule_queue:
                if entry["month"] == month and entry["date"] == date:
                    existing_start = (entry["start_hour"], entry["start_min"])
                    existing_stop = (entry["stop_hour"], entry["stop_min"])
                    if not ((stop_hour, stop_min) <= existing_start or (start_hour, start_min) >= existing_stop):
                        self.devices_text_insert("Error: Overlap with an existing queued schedule.")
                        return

            new_entry = {
                "month": month,
                "date": date,
                "start_hour": start_hour,
                "start_min": start_min,
                "stop_hour": stop_hour,
                "stop_min": stop_min,
                "folder": folder,
                "file": file
            }

            self.schedule_queue.append(new_entry)
            self.devices_text_insert(
                f"[Queued] {month:02d}/{date:02d} | {start_hour:02d}:{start_min:02d} - "
                f"{stop_hour:02d}:{stop_min:02d} | Folder #{folder}, File #{file}"
            )

        except ValueError:
            self.devices_text_insert("Error: Fill all scheduler fields with valid numbers.")


    def send_all_schedules(self):
        """Send all queued schedules to the device (UART or Bluetooth)."""
        if not self.ensure_device_connected():
            self.devices_text_insert("Error: No device connected.")
            return

        if not self.schedule_queue:
            self.devices_text_insert("Error: No schedules queued.")
            return

        try:
            # Command bytes
            start_batch = bytes([0x05])  # Start schedule transmission
            end_batch = bytes([0x0D])    # End schedule transmission

            # Function to encode time (hour and minute) into a single byte
            def encode_time(h, m):
                return ((h & 0b11111) << 3) | (m // 15)  # 5 bits for hour, 3 bits for 15-min intervals

            if self.connection_type.get() == "UART" and self.serial_conn:
                # UART sending
                self.devices_text_insert("[UART][TX] Sending start batch command (0x05)", debug=True)
                self.serial_conn.write(start_batch)

                for sched in self.schedule_queue:
                    encoded_schedule = bytes([
                        sched["month"], sched["date"],
                        encode_time(sched["start_hour"], sched["start_min"]),
                        encode_time(sched["stop_hour"], sched["stop_min"]),
                        sched["folder"], sched["file"]
                    ])
                    self.serial_conn.write(encoded_schedule)
                    self.devices_text_insert(f"[UART][TX] Sent schedule: {encoded_schedule}", debug=True)

                self.serial_conn.write(end_batch)
                self.devices_text_insert("[UART][TX] Sending end batch command (0x0D)", debug=True)
                self.devices_text_insert(f"[UART] Sent {len(self.schedule_queue)} schedule(s) to device.")
                self.schedule_queue.clear()

            elif self.connection_type.get() == "Bluetooth" and self.device_connected:
                # Bluetooth sending
                self.devices_text_insert("[BT][TX] Sending start batch command (0x05)", debug=True)
                self.send_over_bluetooth(start_batch)

                for sched in self.schedule_queue:
                    encoded_schedule = bytes([
                        sched["month"], sched["date"],
                        encode_time(sched["start_hour"], sched["start_min"]),
                        encode_time(sched["stop_hour"], sched["stop_min"]),
                        sched["folder"], sched["file"]
                    ])
                    self.send_over_bluetooth(encoded_schedule)
                    self.devices_text_insert(f"[BT][TX] Sent schedule: {encoded_schedule}", debug=True)

                self.send_over_bluetooth(end_batch)
                self.devices_text_insert("[BT][TX] Sending end batch command (0x0D)", debug=True)
                self.devices_text_insert(f"[BT] Sent {len(self.schedule_queue)} schedule(s) to device.")
                self.schedule_queue.clear()

            else:
                self.devices_text_insert("Error: No valid connection type selected.")

        except Exception as e:
            self.devices_text_insert(f"Error sending schedules: {e}")
        
    def clear_schedule_queue(self):
        """Clear all queued schedules."""
        self.schedule_queue.clear()
        self.devices_text_insert("Schedule queue cleared.")



#main loop
if __name__ == "__main__":
    app = WAPGUI()
    app.mainloop()
