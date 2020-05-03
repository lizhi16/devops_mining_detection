# Crawling dockerhub for all Dockerfile, and checking this Dockerfile whether has malicious behaviors
import sys
import requests
import threading
from bs4 import BeautifulSoup
from get_proxy_ip import get_proxies
from get_proxy_ip import get_url_use_proxy
from malicious_behavior_policies import minerPools
from malicious_behavior_policies import minerTools


basePath = "/N/dc2/scratch/zli10/github_Dockerfile/"
dockerfilePrefix = ["FROM", "MAINTAINER", "RUN", "CMD", "LABEL", "EXPOSE", "ENV", "ADD", "COPY", "ENTRYPOINT", "VOLUME", "USER", "WORKDIR", "ARG", "ONBUILD", "STOPSIGNAL", "HEALTHCHECK", "SHELL", "ONBUILD RUN"]

configFiles = [
    "azure-pipelines.yml",
    ".gitlab-ci.yml",
    "appveyor.yml",
    "codeship-steps.yml",
    ".travis.yml",
    ".cirrus.yml",
    "codefresh.yml",
    "bitrise.yml",
    ".circleci",
    ".platform.app.yaml",
    "solano.yml",
    "wercker.yml",
    "buddy.yml",
    "shippable.yml",
    ".platform.app.yaml",
]

# save the dockerfile
url2dockerfile = {}

class detecting_thread(threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self)
        # github address
        self.github_url = url.strip()
        self.paras = self.github_url.split("/")
        self.github_repo_url = "https://github.com/" + self.paras[3] + "/" + self.paras[4] + "/tree/" + self.paras[6] + "/"

        # file list in github repo
        self.fileList = []

        # Dockerfile
        self.dockerfile = []
        self.Dockerfile = ""

        self.proxy_ip_list = get_proxies()

        # 0: don't contain miner info
        # 1: contain miner info in RUN
        # 2. contain miner info
        # 3. contain config.json in ADD or COPY
        self.classify = 0

        self.command = ""

    def run(self):
        print('[INFO] Start Crawl Thread:', self.github_url)

        #if "Dockerfile" not in self.paras[7]:
        #    return
        """
        if self.github_url != "":
            self.resolve_dockerfile_info()

        if self.Dockerfile != "":
            self.save_Dockerfile()
            self.scan_dockerfile()
        """
        if self.get_github_file_lists() == -1:
            return

        results = ""
        flag = 0
        if len(self.fileList) != 0:
            results, flag = self.check_known_devops_exist()

        if flag == 1 and results != "":
            with open("./repo_Dockerfile_devops.list", "a+") as log:
                log.write(self.github_url + "," + results + "\n")
        elif flag == 1 and results == "":
            with open("./repo_Dockerfile.list", "a+") as log:
                log.write(self.github_url + "," + results + "\n")
        elif flag == 0 and results != "":
            with open("./repo_devops.list", "a+") as log:
                log.write(self.github_url + "," + results + "\n")

        """
        if self.classify == 1 and results != "":
            with open("./miner_in_run_with_known_devops.list", "a+") as log:
                log.write(self.github_url + "," + results + "," + self.command + "\n")
        elif self.classify == 1 and results == "":
            with open("./miner_in_run_with_unknown_devop.list", "a+") as log:
                log.write(self.github_url + "," + self.command + "\n")
        """

    def resolve_dockerfile_info(self):
        # Get Dockerfile in Docker hub
        self.get_Dockerfile()

    def get_Dockerfile(self):
        text = get_url_use_proxy(self.github_url)
        soup = BeautifulSoup(text,'html.parser')
        Commands = soup.find_all('td', class_="blob-code blob-code-inner js-file-line")

        # this web page doesn't contain Dockerfile (maybe)
        if len(Commands) == 0:
            return -2

        dockerfile_flag = 0
        if self.github_url.rsplit("/", 1)[1].strip() == "Dockerfile":
            dockerfile_flag = 1

        command_string = ""
        for command in Commands:
            if command.find('span') != None:
                prefix = command.text.split()
                # sometime, prefix is empty
                if len(prefix) > 0:
                    prefix = prefix[0]
                else:
                    continue

                if command.text.startswith("#"):
                    continue

                # "RUN" ... in command.text
                if prefix in dockerfilePrefix and command_string != "":
                    self.Dockerfile = self.Dockerfile + command_string + "\n"
                    self.dockerfile.append(command_string)
                    # contain content about Dockerfile
                    command_string = command.text.strip().strip('\\')
                # delete the # comment
                elif not command.text.startswith("#"):
                    command_string = command_string + command.text.strip().strip('\\')
            # delete the blank line
            elif command.string.strip() != "":
                if command.text.startswith("#"):
                    continue
                if dockerfile_flag == 0:
                    prefix = command.text.split()
                    if len(prefix) > 0:
                        prefix = prefix[0]
                    else:
                        continue

                    if prefix in dockerfilePrefix and command_string != "":
                        self.Dockerfile = self.Dockerfile + command_string + "\n"
                        self.dockerfile.append(command_string)
                        # contain content about Dockerfile
                        command_string = command.text.strip().strip('\\')
                    elif not command.text.startswith("#"):
                        command_string = command_string + command.text.strip().strip('\\')
                else:
                    command_string = command_string + str(command.string).strip().strip('\\')

        self.Dockerfile = self.Dockerfile + command_string + "\n"
        self.dockerfile.append(command_string)

        return 1

    def save_Dockerfile(self):
        if self.Dockerfile != "":
            url2dockerfile[self.github_url] = self.Dockerfile

    def scan_dockerfile(self):
        if len(self.dockerfile) == 0:
            return

        for command in self.dockerfile:
            if "RUN" in command:
                self.classify = 1
                self.command = command
                break

    def get_github_file_lists(self):
        text = get_url_use_proxy(self.github_repo_url)
        if text == "":
            return -1
        soup = BeautifulSoup(text,'html.parser')
        links = soup.find_all('tr',class_="js-navigation-item")

        for link in links:
            try:
                fileType = link.find('svg')['aria-label']
                fileName = link.find('a', class_="js-navigation-open")['title']
                # "/" will not show in file name
                self.fileList.append(fileType + "/" + fileName)
            except:
                continue

        return 1

    def check_known_devops_exist(self):
        results = ""
        flag = 0
        for file in self.fileList:
            fileName = file.split("/")[1]
            if fileName in configFiles:
                if results == "":
                    results = results + fileName
                else:
                    results = results + "; " + fileName
            if "Dockerfile" in fileName:
                flag = 1
        return results, flag

def main():
    cores = 48

    urls = open(sys.argv[1], "r").readlines()
    analyze_thread = []
    for url in urls:
        if "https" not in url:
            continue
        thread = detecting_thread(url)
        # keep the threads < cores numbers
        if len(threading.enumerate()) <= cores:
            thread.start()
            analyze_thread.append(thread)
        else:
            for t in analyze_thread:
                t.join()

            thread.start()
            analyze_thread.append(thread)

    for t in analyze_thread:
        t.join()

    # save all dockerfile in file
    #with open(basePath + "url2dockerfile-" + sys.argv[1] + ".json", 'w+') as f:
    #    json.dump(url2dockerfile, f, ensure_ascii=True)

if __name__ == '__main__':
    main()
