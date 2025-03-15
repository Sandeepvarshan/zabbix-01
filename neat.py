import subprocess
import csv
import re

def adb_command(adb_path, command):
    """Executes an ADB command and returns the output."""
    full_command = [adb_path] + command.split()
    try:
        result = subprocess.run(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

def connect_to_device(adb_path, ip_address):
    """Connect to the Android device using its IP address and port."""
    command = f"connect {ip_address}:4242"
    output, error = adb_command(adb_path, command)
    return output, error

def is_valid_ip(ip_address):
    """Validate the IP address format."""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    return re.match(pattern, ip_address) is not None

def main():
    # ADB executable path
    adb_path = r'C:\Users\NSandeepVarshan\AppData\Local\Android\Sdk\platform-tools\adb.exe'
    
    # Port number
   

    # List to hold connected devices
    connected_devices = []

    # CSV file path
    csv_file_path = r'zab samp\Poly,yealink,logi-host.csv'
    
    # Read the CSV file
    with open(csv_file_path, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Get the IP address from the 'udid' field
            ip_address = row.get('udid')
            
            # Validate the IP address
            if ip_address and is_valid_ip(ip_address):
                print(f"Connecting to {ip_address}...")
                output, error = connect_to_device(adb_path, ip_address)
                
                if error:
                    print(f"Cannot connect to {ip_address}: {error}")
                else:
                    connected_devices.append(f"{row['Host']} - {ip_address} - connected")
                    print(f"Successfully connected to {ip_address}: {output}")
            else:
                print(f"Invalid IP address format: {ip_address}")

    # Print the connected devices
    if connected_devices:
        print("\nSuccessfully connected devices:")
        for device in connected_devices:
            print(device)

    print("ADB connection attempts complete.")

if __name__ == "__main__":
    main()

