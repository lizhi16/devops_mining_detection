# Crawling dockerhub for all Dockerfile, and checking this Dockerfile whether has malicious behaviors
import sys
import time
import requests
import threading

mining_info = [
    " H/s",
    " h/s",
    " khash/s",
    " kHash/s",
    "2.5s/60s/15m",
    "Mining coin:",
    "MEMORY ALLOC FAILED",
    #"CPU mining",
    #"wallet address",
    #"hashrate",
    "connected. Logging in",
    "New block detected",
    "Difficulty changed",
    "CPU: Share accepted",
    "COMMANDS     hashrate, pause, resume",
    "speed 10s/60s/15m",
]

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
        return content.text
    else:
        print ("[ERROR] Can't resolve url:", url)
        return None

def mining_analyze(log):
    rate = 0
    key = []
    for keyword in mining_info:
        if keyword in log:
            rate = rate + 1
            key.append(keyword)

    return rate, key

def resolve_repo_address(content):
    address = ""
    author = ""
    for line in content.split("\n"):
        if "git clone --depth=50" in line:
            address = line.strip().rsplit(" ", 2)[1]
            author = line.strip().rsplit(" ", 1)[1]

    return address, author

travis_url = "https://api.travis-ci.org/v3/job/{}/log.txt"
savePath_travis = "./analyze_log/travis-repos.csv"
class travis_threading(threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self)
        self.url = url

    def run(self):
        flag = self.travis_log_analysis()
        if flag == -1:
            print ("[ERR] not get:", self.index)
        elif flag == 0:
            print ("[WARN] not have:", self.index)

    def travis_log_analysis(self):
        content = get_url_content(self.url)

        if content == None:
            return -1

        if "Sorry, we experienced an error." in content:
            return 0

        results, key = mining_analyze(content)
        repos, author = resolve_repo_address(content)
        if repos != "" and results != 0:
            print("[INFO] Get the target:", repos, results)
            with open(savePath_travis, "a+") as log:
                log.write(author + ", " + self.url + "\n")
            with open("./second-level-scan/travis-repos.csv", "a+") as log:
                log.write(author + ", " + self.url + ", " + str(results) + "," + str(key) + "\n")
        return 1

def start_analyze_travis():
    analyze_thread = []
    for line in open(sys.argv[1], "r").readlines():
        thread = travis_threading(line.strip().split(",")[1])
        print ("[INFO] Start to get url:", line.strip().split(",")[1])
        # keep the threads < cores numbers
        if len(threading.enumerate()) <= 30:
            thread.start()
            analyze_thread.append(thread)
        else:
            for t in analyze_thread:
                t.join()

            thread.start()
            analyze_thread.append(thread)

    for t in analyze_thread:
        t.join()

savePath_circleci = "./analyze_log/circleci-repos.csv"
def start_analyze_circleci():
    for line in open(sys.argv[1], "r").readlines():
        author = line.split("/")[7] + "/" + line.split("/")[8]
        url = line.strip().split(",")[1]
        with open(savePath_circleci, "a+") as log:
            log.write(author + ", " + url + "\n")

if __name__ == '__main__':
    if sys.argv[2] == "circleci":
        start_analyze_circleci()
    elif sys.argv[2] == "travis":
        start_analyze_travis()

# circleci
# https://circleci.com/api/v1.1/project/github/dajiejie123/webserver/{build的次数}/output/{}/0?file=true
# wercker
# https://app.wercker.com/api/v3/workflows/577a5a643828f9673b0459d5
