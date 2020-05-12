import sys
import time
import requests
import threading
from malicious_behavior_policies import minerTools
from malicious_behavior_policies import minerPools

basePath = "./results/"

class detecting_thread(threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self)
        self.githubUrl = url
        self.paras = url.strip().split("/")
        # repo info
        self.author = self.paras[3]
        self.project = self.paras[4]
        self.hash = self.paras[6]
        self.fileName = url.rsplit("/", 1)[1].strip()
        self.fileUrl = "https://raw.githubusercontent.com/" + self.author + "/" + self.project + "/" + self.hash + "/" + self.fileName

        # content of the target content
        self.fileContent = ""

    def run(self):
        print('[INFO] Start Crawl Thread:', self.githubUrl)

        # get the content of target file
        content =  get_url_content(self.fileUrl)
        if content != None:
            self.fileContent = content.text

        if self.analyze_file_content() == -1:
            print ("[WARN] can't get the content:", self.fileUrl)

    def analyze_file_content(self):
        if self.fileContent == "":
            print ("[ERROR] The content is empty...")
            return -1

        tool, pool = check_miner_info(self.fileContent)
        images, scripts = check_docker_image_info(self.fileContent)

        fileName = self.fileName.strip(".").split(".")[0]
        if tool == 1 or pool == 1:
            with open(basePath + "miner_in_file-" + fileName + ".list", "a+") as log:
                log.write(self.githubUrl + "\n")

        if len(images) != 0:
            images_list = open(basePath + "images-" + fileName + ".list", "a+")
            with open(basePath + "images_in_file-" + fileName + ".list", "a+") as log:
                log.write(self.githubUrl + "\n")
                for image in images:
                    log.write(image + "\n")
                    images_list.write(image + "\n")
            images_list.close()

        if len(scripts) != 0:
            with open(basePath + "scripts-" + fileName + ".list", "a+") as log:
                log.write(self.githubUrl + "\n")
                for script in scripts:
                    log.write(script + "\n")

# get the miner info in the content
def check_miner_info(content):
    toolFlag = 0
    for tool in minerTools:
        if tool in content:
            toolFlag = 1

    poolFlag = 0
    for pool in minerPools:
        if pool in content:
            poolFlag = 1

    return toolFlag, poolFlag

# get the docker image in the content
def check_docker_image_info(content):
    illegal = ['=', ",", "\'", "#", "+", "$", "@", "[", "]", "(", ")", "-", "\""]
    images = []
    scripts = []
    content = content.replace("\\n", "")
    for line in content.split("\n"):
        # contain docker run command
        if "docker run " in line and not line.startswith("#"):
            paras = line.split(" ")
            for i in range(len(paras)):
                if paras[i].count('/') == 1 and paras[i].split('/')[0] != "" and paras[i].split('/')[1] != "":
                    flag = 0
                    for bad in illegal:
                        if bad in paras[i]:
                            flag = 1
                    if flag == 0:
                        images.append(paras[i].strip())

        # .azure-pipelines.yml and azure-pipelines.yml
        if "ci_runner_image:" in line and not line.startswith("#"):
            if "/" in line.split(":")[1].strip():
                images.append(line.split(":")[1].strip())

        if "image:" in line and "$" not in line.split(":")[1] and not line.startswith("#"):
            if "/" in line.split(":")[1].strip():
                images.append(line.split(":")[1].strip())

        # wercker.yml
        if line.startswith("box:"):
            if "/" in line.split(":")[1].strip():
                images.append(line.split(":")[1].strip())

        if "docker_image_name:" in line:
            if "/" in line.split(":")[1].strip():
                images.append(line.split(":")[1].strip())

        # get scripts
        if ".sh " in line or line.endswith(".sh"):
            for item in line.split(" "):
                if ".sh" in item:
                    scripts.append(item)

    return list(set(images)), list(set(scripts))

# get the content from a url
def get_url_content(url):
    headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    content = requests.get(url,headers=headers)

    # WARN: for high frequency requests
    while content.status_code == 429:
        print("[WARN] High frequncy requests!")
        time.sleep(60)
        content = requests.get(url,headers=headers)

    if content.status_code == 200:
        return content
    else:
        print ("[ERROR] Can't resolve url:", url)
        return None

def main():
    cores = 10

    images = open(sys.argv[1], "r").readlines()
    analyze_thread = []
    for image in images:
        if "http" not in image:
            continue
        thread = detecting_thread(image.strip())
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

if __name__ == '__main__':
    main()
