import subprocess
import time
import threading
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
ADB_KEY_PATH = r'C:\Users\v-svarshann\.android\adbkey'
ADB_PUB_KEY_PATH = r'C:\Users\v-svarshann\.android\adbkey.pub'
CSV_FILE_PATH = r'Poly,yealink,logi-host.csv'
BASE_URL = "https://{device_ip}/web/"
USERNAME = "admin"
PASSWORD = "Admin@123"


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


def setup_web_driver():
    """Setup Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    return webdriver.Chrome(options=options)


def paste_public_key(public_key, driver, device_ip):
    """Paste the public key into the Webex Developer API page using Selenium."""
    device_url = BASE_URL.format(device_ip=device_ip)
    print(f"Navigating to the device page: {device_url}")
    driver.get(device_url)

    try:
        # Login
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
        password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password")))
        password_field.send_keys(PASSWORD)
        password_field.send_keys(Keys.RETURN)
        print("Logged into the device.")

        # Navigate to Developer API
        dev_api_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//nav//a[contains(text(),'Developer API')]"))
        )
        dev_api_button.click()
        print("Opened Developer API page.")

        # Paste public key
        input_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//textarea")))
        input_field.send_keys(f'xCommand SystemUnit Extension Adb Enable Key: "{public_key}"')
        print("Pasted public key.")

        # Click Apply
        apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Apply']"))
        )
        apply_button.click()
        print("Clicked Apply button. Public key applied successfully.")
    except Exception as e:
        print(f"Error during Selenium interactions: {e}")


def disconnect_adb(device_ip):
    """Disconnect from the ADB device."""
    time.sleep(120)  # Wait for 2 minutes
    disconnect_command = f'adb disconnect {device_ip}'
    print(f"Disconnecting from {device_ip}...")
    execute_adb_command(disconnect_command)


def read_device_ips_from_csv(file_path):
    """Read the device IPs (UDID) from a CSV file."""
    device_ips = []
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'udid' in row and row['udid'].strip():
                    device_ips.append(row['udid'].strip())
                else:
                    print(f"Skipping invalid or missing IP in row: {row}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return device_ips


def capture_logs(device_ip):
    """Capture logs from the connected ADB device."""
    log_command = f'adb -s {device_ip} logcat -d'
    print("Capturing logs...")
    logs = execute_adb_command(log_command)
    if logs:
        log_file_path = f"{device_ip}_logs.txt"
        with open(log_file_path, 'w') as log_file:
            log_file.write(logs)
        print(f"Logs saved to {log_file_path}")
    else:
        print("No logs captured.")


def main():
    """Main execution flow."""
    generate_adb_key(ADB_KEY_PATH)
    public_key = read_public_key(ADB_PUB_KEY_PATH)
    print(f"Public Key:\n{public_key}")

    device_ips = read_device_ips_from_csv(CSV_FILE_PATH)
    print("ip",device_ips)
    if not device_ips:
        print("No valid device IPs found in the CSV file.")
        return

    # Initialize Selenium WebDriver
    driver = setup_web_driver()
    try:
        for device_ip in device_ips:
            print(f"Processing device at IP: {device_ip}...")
            paste_public_key(public_key, driver, device_ip)

            print("Restarting ADB server...")
            execute_adb_command('adb kill-server')
            execute_adb_command('adb start-server')

            # Connect to the device
            print(f"Connecting to device IP: {device_ip}...")
            connect_command = f'adb connect {device_ip}'
            execute_adb_command(connect_command)

            # Capture logs
            capture_logs(device_ip)

            # Start disconnection thread
            disconnect_thread = threading.Thread(target=disconnect_adb, args=(device_ip,))
            disconnect_thread.start()
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
