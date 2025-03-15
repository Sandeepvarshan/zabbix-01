import csv
import subprocess
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def execute_adb_command(command):
    """Execute an ADB command and print the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command '{command}': {e.stderr}")
        return None


def generate_adb_key(key_path):
    """Generate ADB key."""
    keygen_command = f'adb keygen {key_path}'
    print("Generating ADB key...")
    execute_adb_command(keygen_command)


def read_public_key(pub_key_path):
    """Read the generated public key."""
    print("Reading public key...")
    with open(pub_key_path, 'r') as file:
        return file.read().strip()


def navigate_to_developer_api(driver):
    """Navigate to the home page and then to the Developer API page."""
    driver.get("https://{device_ip}/web/")  # Change to the appropriate URL
    time.sleep(5)  # Wait for the page to load


def paste_public_key(public_key):
    """Paste the public key into the Webex Developer API page using Selenium."""
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')

    driver = webdriver.Chrome(options=options)
    navigate_to_developer_api(driver)

    username_field = driver.find_element(By.ID, "username")  # Replace with actual ID
    password_field = driver.find_element(By.ID, "password")  # Replace with actual ID

    username_field.send_keys("admin")
    password_field.send_keys("Admin@123")
    password_field.send_keys(Keys.RETURN)
    time.sleep(10)  # Wait for login to complete

    dev_api_button = driver.find_element(By.XPATH, "/html/body/div/div/nav/div[2]/a[7]")
    if dev_api_button.is_displayed():
        dev_api_button.click()
        print('Developer button is clicked')
    else:
        print('Something went wrong')

    time.sleep(5)

    input_field = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div[2]/textarea")
    input_field.send_keys("xCommand SystemUnit Extension Adb Enable Key:" + '"' + public_key + '"')
    time.sleep(10)
    button_click = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div[2]/p[2]/button")
    button_click.click()
    time.sleep(6)

    return driver


def disconnect_adb(device_ip):
    """Disconnect from the ADB device after 2 minutes."""
    time.sleep(120)  # Wait for 2 minutes
    disconnect_command = f'adb disconnect {device_ip}'
    print(f"Disconnecting from {device_ip}...")
    execute_adb_command(disconnect_command)


def capture_logs(device_ip):
    """Capture logs from the connected ADB device."""
    log_command = f'adb -s {device_ip} logcat -d'
    print("Capturing logs from device...")
    logs = execute_adb_command(log_command)
    if logs:
        log_file_path = f"{device_ip}_device_logs.txt"
        with open(log_file_path, 'w') as log_file:
            log_file.write(logs)
        print(f"Logs saved to {log_file_path}")
    else:
        print("No logs captured.")


def read_device_ips_from_csv(csv_file_path):
    """Read device IPs from a CSV file."""
    device_ips = []
    try:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'udid' in row:  # Assuming 'udid' is the column name for device IPs
                    device_ips.append(row['udid'])
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return device_ips


def main():
    adb_key_path = r'C:\Users\v-svarshann\.android\adbkey'
    adb_pub_key_path = r'C:\Users\v-svarshann\.android\adbkey.pub'
    csv_file_path = 'Poly,yealink,logi-host.csv'  # Path to your CSV file

    generate_adb_key(adb_key_path)
    public_key = read_public_key(adb_pub_key_path)
    print(f"Public Key:\n{public_key}")

    driver = paste_public_key(public_key)
    driver.quit()

    print("Restarting ADB server...")
    execute_adb_command('adb kill-server')
    execute_adb_command('adb start-server')

    device_ips = read_device_ips_from_csv(csv_file_path)
    if not device_ips:
        print("No device IPs found in the CSV file.")
        return

    for device_ip in device_ips:
        print(f"Connecting to device IP: {device_ip}...")
        connect_command = f'adb connect {device_ip}'
        execute_adb_command(connect_command)

        # Capture logs for the device
        capture_logs(device_ip)

        # Start a thread to disconnect after 2 minutes
        disconnect_thread = threading.Thread(target=disconnect_adb, args=(device_ip,))
        disconnect_thread.start()


if __name__ == "__main__":
    main()