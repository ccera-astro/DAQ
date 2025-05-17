import serial
import time

class NumatoGPIO:
    def __init__(self, port, num_outputs=8, baudrate=115200, timeout=1):
        self.port = port
        self.num_outputs = num_outputs
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None

    def connect(self):
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(0.1) # Allow time for the connection to establish
            self.serial_connection.write("gpio iodir 00\r".encode())
            dmy = self.serial_connection.read(20)
            self.clear_outputs()
            return True
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            return False

    def disconnect(self):
         if self.serial_connection and self.serial_connection.is_open:
            self.clear_outputs()
            self.serial_connection.close()

    def write_output(self, output_number, value):
        if not self.serial_connection or not self.serial_connection.is_open:
            print("Serial port not open. Connect first.")
            return

        if not 0 <= output_number < self.num_outputs:
            raise ValueError(f"Output number must be between 0 and {self.num_outputs - 1}")

        if value not in [0, 1]:
            raise ValueError("Value must be 0 or 1")

        command = f"gpio write {output_number} {value}\r".encode('utf-8')
        self.serial_connection.write(command)
        self.serial_connection.flush()
        # This version doesn't produce an "OK", just another ">" prompt
        #
        response = self.serial_connection.read(20).decode('utf-8')
        if (">" not in response):
            print ("No '>' in response. Oh well")
    
    def write_all_outputs(self, value):
         if not self.serial_connection or not self.serial_connection.is_open:
            print("Serial port not open. Connect first.")
            return
         if not 0 <= value <= (2**self.num_outputs - 1):
            raise ValueError(f"Value must be between 0 and {2**self.num_outputs - 1}")
         
         hex_value = hex(value)[2:].zfill(self.num_outputs // 4) # Ensure correct number of hex digits
         command = f"gpio writeall {hex_value}\r".encode('utf-8')
         self.serial_connection.write(command)
         self.serial_connection.flush()
         response = self.serial_connection.read(20).decode('utf-8')
         if ">" not in response.lower():
             print("No '>' in response.  Oh well")

    def clear_outputs(self):
        self.write_all_outputs(0)
