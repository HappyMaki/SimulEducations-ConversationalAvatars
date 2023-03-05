import subprocess
import requests
import os
import json
import zipfile


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
        print("Current Version: " + self.current_version)
        print("Latest Version: " + self.latest_release_version)
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
                    print(e)
        self.updateLocalVersionNumber()

    def downloadLatestRelease(self):
        build_path = "StandaloneWindows64"
        self.cleanLocal(build_path)
        if os.path.exists(build_path):
            os.removedirs(build_path)

        self.local_filename = os.path.join(self.temp_dir, self.latest_release_url.split("/")[-1])
        r = requests.get(self.latest_release_url, allow_redirects=True)
        print(f"Downloaded: {int(r.headers.get('content-length'))/1024/1024} MB")
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
        print("Cleaning Local Files")
        self.cleanLocal(self.temp_dir)

        print("Downloading")
        self.downloadLatestRelease()

        print("Unzipping")
        self.unzipLatestRelease()

        print("Cleaning temp files")
        self.deleteZip()

def startGame():
    print("Starting Game")
    subprocess.Popen(["StandaloneWindows64/Lincoln Conversational AI.exe"])
    os._exit(0)
    pass

def main():
    versionUtil = VersionUtil("https://api.github.com/repos/HappyMaki/SimulEducations-ConversationalAvatars-Releases/releases")
    if versionUtil.isNewVersionAvailable():
        print(f"Current Version: {versionUtil.current_version}")
        print(f"Latest Available Version: {versionUtil.latest_release_version}")

        versionUtil.getLatestVersion()
        versionUtil.promoteTempToMain()
        versionUtil.cleanLocal("temp")
        versionUtil.updateLocalVersionNumber()

        print(f"Manual Download Url: {versionUtil.latest_release_url}")

    del(versionUtil)

    versionUtil = VersionUtil("https://api.github.com/repos/HappyMaki/SimulEducations-ConversationalAvatars-Releases/releases")
    if not versionUtil.isNewVersionAvailable():
        startGame()
    else:
        raise Exception("Failed to get new version. Please get it directly from https://github.com/HappyMaki/SimulEducations-ConversationalAvatars-Releases")


if __name__ == "__main__":
    main()
