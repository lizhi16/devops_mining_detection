# Crawling dockerhub for all Dockerfile, and checking this Dockerfile whether has malicious behaviors
import sys
import time
import requests
import threading

mining_info = [
    " H/s ",
    " h/s",
    " khash/s",
    " kHash/s",
    "2.5s/60s/15m",
    "Mining coin:",
    "MEMORY ALLOC FAILED",
    #"CPU mining",
    "wallet address",
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

travis_url = "https://api.travis-ci.org/v3/job/{}/log.txt"
savePath_travis = "./results/travis-strong-scan.csv"
class travis_threading(threading.Thread):
    def __init__(self, index):
        threading.Thread.__init__(self)
        self.index = index

    def run(self):
        flag = self.travis_log_analysis()
        if flag == -1:
            print ("[ERR] not get:", self.index)
        elif flag == 0:
            print ("[WARN] not have:", self.index)

    def travis_log_analysis(self):
        url = travis_url.format(str(self.index))
        content = get_url_content(url)

        if content == None:
            return -1

        if "Sorry, we experienced an error." in content:
            return 0

        results, key = mining_analyze(content)
        if results != 0:
            with open(savePath_travis, "a+") as log:
                log.write(str(results) + ", " + self.url + "," + str(keyword) + "\n")
        return 1

def start_analyze_travis():
    analyze_thread = []
    for i in range(int(sys.argv[1]), int(sys.argv[2])):
        thread = travis_threading(i)
        # keep the threads < cores numbers
        if len(threading.enumerate()) <= 100:
            thread.start()
            analyze_thread.append(thread)
        else:
            for t in analyze_thread:
                t.join()

            thread.start()
            analyze_thread.append(thread)

    for t in analyze_thread:
        t.join()


savePath_circleci = "./results/circleci-strong-scan.csv"
class circleci_thread(threading.Thread):
    def __init__(self, url, repo):
        threading.Thread.__init__(self)
        self.repo = repo
        self.url = url

    def run(self):
        flag = self.circleci_log_analysis()
        if flag == -1:
            print ("[ERR] not exist:", self.author, self.repo)

    def circleci_log_analysis(self):
        content = get_url_content(self.url)

        if content == None:
            return -1

        results, key = mining_analyze(content)

        if results != 0:
            with open(savePath_circleci, "a+") as log:
                log.write(str(results) + ", " + self.url + "," + str(key) + "\n")
        return 1

def start_analyze_circleci():
    analyze_thread = []
    repolist = open(sys.argv[1], "r")
    for line in repolist.readlines():
        repo = line.split(",")[0]
        url = line.strip().split(",")[1]

        thread = circleci_thread(url, repo)
        # keep the threads < cores numbers
        if len(threading.enumerate()) <= 10:
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
    start_analyze_circleci()
    #start_analyze_travis()

# circleci
# https://circleci.com/api/v1.1/project/github/dajiejie123/webserver/{build的次数}/output/{}/0?file=true
# wercker
# https://app.wercker.com/api/v3/workflows/577a5a643828f9673b0459d5
