"""
Simple script that utilizes VirusTotals API to scan local
files for viruses. An installer is available for
this script that adds it to your context menu so that scanning
a file doesn't require more than two clicks.
virustotal API refrence: https://developers.virustotal.com/v2.0/reference
"""

import hashlib
from requests import get, post, RequestException
from sys import exit, argv
from pymsgbox import alert, prompt
from os import path, getenv, startfile
from TrayMessage import WindowsBalloonTip


class Scan:
    def __init__(self, program, api_key):
        self.program_name = program.split("\\")[-1]
        self.checksum = md5(program)
        self.url = "https://www.virustotal.com/vtapi/v2/file/report"
        self.response = ""
        self.api_key = api_key

    def vp_scan(self):
        params = {'apikey': self.api_key, 'resource': self.checksum}

        # try except to prevent generic error message and provide a more descriptive message
        try:
            response = get(self.url, params=params)
            self.response = response.json()
        except RequestException:
            balloon_tip("No internet", "Internet is required to scan application!", 5)
            exit(1)
        except ValueError:
            balloon_tip("No results", "There might be a problem with your API key or scanning frequency.", 5)
            exit(1)

        if "scans" not in self.response:
            balloon_tip("Checksum not in database", self.response["verbose_msg"], 5)
            exit(1)

        balloon_tip("Scan finished",
                    "Detection ratio: " + str(self.response["positives"]) + "/" + str(self.response["total"]) +
                    "\nFull report written to C:\\Users\\{}\\Scan report of {}.txt".format(USERNAME, self.program_name), 10)

    def write_to_file(self):
        """Write a more detailed report of scan to file"""
        scan_report = open(r"C:\Users\{}\Scan report of {}.txt".format(USERNAME, self.program_name), "a")

        for scan in self.response["scans"]:
            scan_report.write("%-20s" % scan + " - Detection: " + str(self.response["scans"][scan]["detected"]))
            if self.response["scans"][scan]["detected"]: scan_report.write(" (%s)" % self.response["scans"][scan]["result"])
            scan_report.write("\n")

        scan_report.write("\nDetection ratio: " + str(self.response["positives"]) + "/" + str(self.response["total"]))
        scan_report.close()


class Upload:
    def __init__(self, program, api_key):
        self.program_name = program.split("\\")[-1]
        self.program_path = program
        self.url = "https://www.virustotal.com/vtapi/v2/file/scan"
        self.api_key = api_key

    def vp_upload(self):
        params = {'apikey': self.api_key}
        files = {'file': (self.program_path, open(self.program_path, 'rb'))}

        # try except to prevent generic error message and provide a more descriptive message
        try:
            response = post(self.url, files=files, params=params)
            response = response.json()
        except RequestException:
            balloon_tip("No internet", "Internet is required to upload a file!", 5)
            exit(1)
        except ValueError:
            balloon_tip("No results", "There might be a problem with your API key.", 5)
            exit(1)

        startfile(response["permalink"])
        balloon_tip("Successfully uploaded", response["verbose_msg"], 10)


def balloon_tip(title, msg, length):
    """Pop-up messagebox"""
    #MessageBox = WindowsBalloonTip()
    MessageBox.ShowWindow(title, msg, length)


def md5(file_name):
    """Gets file checksum"""
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def add_api_key(message, title):
    api_key_path = open(API_PATH, "w")
    alert(message, title)
    key = prompt('Public API key:')
    # re-prompt user until the key is valid (by checking length)
    try:
        if len(key) != 64: add_api_key("Invalid key entered. Please re-enter public key", "Invalid key entered")
    except TypeError:
        exit(0)

    api_key_path.write(key)
    api_key_path.close()


if __name__ == "__main__":
    if len(argv) != 3: exit(1)  # exits if it is not started from context menu

    FILE = argv[1]
    USERNAME = getenv('username')
    API_PATH = r"C:\Users\{}\vt_public_api".format(USERNAME)  # put key in this folder to prevent issues with permissions

    MessageBox = WindowsBalloonTip()  # for balloon_tip function

    # if api key is not present on the computer, add it
    if not path.exists(API_PATH):
        add_api_key("Please enter your public API key", "Public API key required")
    elif len(open(API_PATH, "r").read()) != 64:
        add_api_key("API key found, but not valid. Please re-enter public key.", "Public API key required")

    API_KEY = open(API_PATH).read()

    if argv[2] == "Upload":
        balloon_tip("Upload starting", "Upload has started. This will take a few minutes.", 4)
        VirusTotalUpload = Upload(FILE, API_KEY)
        VirusTotalUpload.vp_upload()
    else:
        balloon_tip("Scan starting", "Scan has started. This should not take very long.", 4)
        VirusTotalScan = Scan(FILE, API_KEY)
        VirusTotalScan.vp_scan()
        VirusTotalScan.write_to_file()
