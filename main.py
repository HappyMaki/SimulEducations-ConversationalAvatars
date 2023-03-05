import subprocess
import requests
import os
import json
import zipfile
import time
import threading
import logging
import tkinter as tk # Python 3.x
import tkinter.scrolledtext as ScrolledText
from pathlib import Path
import shutil
from google.cloud import storage


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys/wired-analogy-379505-261371efaf56.json"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to upload is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the if_generation_match precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    generation_match_precondition = 0

    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name}."
    )


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

class myGUI(tk.Frame):

    # This class defines the graphical user interface

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.build_gui()

    def build_gui(self):
        # Build GUI
        self.root.title('TEST')
        self.root.option_add('*tearOff', 'FALSE')
        self.grid(column=0, row=0, sticky='ew')
        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')

        # Add text widget to display logging info
        st = ScrolledText.ScrolledText(self, state='disabled')
        st.configure(font='TkFixedFont')
        st.grid(column=0, row=1, sticky='w', columnspan=4)

        # Create textLogger
        text_handler = TextHandler(st)

        # Logging configuration
        logging.basicConfig(filename='test.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s')

        # Add the handler to logger
        logger = logging.getLogger()
        logger.addHandler(text_handler)

def worker():
    # Skeleton worker function, runs in separate thread (see below)
    upload_logs_to_gcs()
    main_patcher()

class VersionUtil:
    def __init__(self, gitReleaseUrl):
        self.temp_dir = "temp"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        self.latest_release_version, self.latest_release_url = self.getLatestVersionNumber(gitReleaseUrl)
        self.current_version = self.getCurrentVersionNumber()


    def getReleaseInformation(self, gitReleaseUrl):
        payload={}
        headers = {}

        response = requests.request("GET", gitReleaseUrl, headers=headers, data=payload)

        return json.loads(response.text)

    def isNewVersionAvailable(self):
        logging.info("Current Version: " + self.current_version)
        logging.info("Latest Version: " + self.latest_release_version)
        return self.current_version != self.latest_release_version


    def getLatestVersionNumber(self, gitReleaseUrl):
        releases_json = self.getReleaseInformation(gitReleaseUrl)
        for release in releases_json:
            if release.get("tag_name") == "latest":
                release_version = release.get("name")[10:].replace(".zip", f"{release.get('id')}") + "_" + release.get("assets")[0].get("updated_at")
                release_download_url = release.get("assets")[0].get("browser_download_url")
                return release_version, release_download_url
        raise Exception(f"Could not find or parse release information from {gitReleaseUrl}")

    def getCurrentVersionNumber(self):
        f = open("version.txt", "r")
        version = "".join(f.readlines())
        f.close()
        return version

    def updateLocalVersionNumber(self, dir=""):
        f = open(os.path.join(dir, "version.txt"), "w")
        f.write(self.latest_release_version)
        f.close()

    def cleanLocal(self, dir):
        if os.path.exists(dir):
            for the_file in os.listdir(dir):
                file_path = os.path.join(dir, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    else:
                        self.cleanLocal(file_path)
                        os.rmdir(file_path)
                except Exception as e:
                    logging.info(e)
        self.updateLocalVersionNumber()

    def downloadLatestRelease(self):
        build_path = "StandaloneWindows64"
        self.cleanLocal(build_path)
        if os.path.exists(build_path):
            os.removedirs(build_path)

        self.local_filename = os.path.join(self.temp_dir, self.latest_release_url.split("/")[-1])
        r = requests.get(self.latest_release_url, allow_redirects=True)
        logging.info(f"Downloaded: {int(r.headers.get('content-length'))/1024/1024} MB")
        open(self.local_filename, 'wb').write(r.content)

    def unzipLatestRelease(self):
        with zipfile.ZipFile(self.local_filename, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

    def deleteZip(self):
        os.remove(self.local_filename)

    def promoteTempToMain(self):
        main_path = "StandaloneWindows64"
        # if not os.path.exists(main_path):
        #     os.makedirs(main_path)
        os.rename(self.temp_dir, main_path)


    def getLatestVersion(self):
        logging.info("Cleaning Local Files")
        self.cleanLocal(self.temp_dir)

        logging.info("Downloading")
        self.downloadLatestRelease()

        logging.info("Unzipping")
        self.unzipLatestRelease()

        logging.info("Cleaning temp files")
        self.deleteZip()

def startGame():
    logging.info("Starting Game")
    subprocess.Popen(["StandaloneWindows64/Lincoln Conversational AI.exe"])
    os._exit(0)
    pass

def main_patcher():
    versionUtil = VersionUtil("https://api.github.com/repos/HappyMaki/SimulEducations-ConversationalAvatars-Releases/releases")
    if versionUtil.isNewVersionAvailable():
        logging.info(f"Current Version: {versionUtil.current_version}")
        logging.info(f"Latest Available Version: {versionUtil.latest_release_version}")

        versionUtil.getLatestVersion()
        versionUtil.promoteTempToMain()
        versionUtil.cleanLocal("temp")
        versionUtil.updateLocalVersionNumber()

        logging.info(f"Manual Download Url: {versionUtil.latest_release_url}")

    del(versionUtil)

    versionUtil = VersionUtil("https://api.github.com/repos/HappyMaki/SimulEducations-ConversationalAvatars-Releases/releases")
    if not versionUtil.isNewVersionAvailable():
        startGame()
    else:
        raise Exception("Failed to get new version. Please get it directly from https://github.com/HappyMaki/SimulEducations-ConversationalAvatars-Releases")

def setup_tkinter():
    root = tk.Tk()
    myGUI(root)

    t1 = threading.Thread(target=worker, args=[])
    t1.start()

    root.mainloop()
    t1.join()

def upload_logs_to_gcs():
    logging.info("uploading logs to cloud")

    src_path = r"chatlogs.txt"
    timestamp = str(time.time()).split(".")[0]
    dst_path = f"old-logs/chatlogs_{timestamp}.txt"
    path = Path(src_path)
    logging.info(path.is_file())
    if path.is_file():
        logging.info(f"File found: {src_path}")
        shutil.move(src_path, dst_path)

        upload_blob("conversational-ai-avatars", dst_path, f"chat-logs/no-account/chatlogs_{timestamp}.txt")


if __name__ == "__main__":
    setup_tkinter()
