# Please using crawl_suspect_repo_list.py firstly to get repo list
# This script used to Download the list of github repos
# which contains the DevOps platforms' config files
# and analyze this repo whether contains mining code
import os
import re
import csv
import threading
import subprocess

repoList_Dockerfile = [
    "repoList_appveyor_2018-01-01.txt",
    "repoList_appveyor_Dockerfile_2018-01-01.txt",
    "repoList_azure_2018-01-01.txt",
    "repoList_azure_Dockerfile_2018-01-01.txt",
    "repoList_bitrise_2018-01-01.txt",
    "repoList_bitrise_Dockerfile_2018-01-01.txt",
    "repoList_cirrus_2018-01-01.txt",
    "repoList_cirrus_Dockerfile_2018-01-01.txt",
    "repoList_codefresh_2018-01-01.txt",
    "repoList_codefresh_Dockerfile_2018-01-01.txt",
    "repoList_codeship_2018-01-01.txt",
    "repoList_codeship_Dockerfile_2018-01-01.txt",
    "repoList_gitlab_2018-01-01.txt",
    "repoList_gitlab_Dockerfile_2018-01-01.txt",
    "repoList_travis_2018-01-01.txt",
    "repoList_travis_Dockerfile_2018-01-01.txt"
]

minerPools = [
    "aeon-pool.com",
    "alimabi.cn",
    "backup-pool.com",
    "bohemianpool.com",
    "coinedpool.com",
    "coinmine.pl",
    "cryptity.com",
    "cryptmonero.com",
    "crypto-pool.fr",
    "crypto-pools.org",
    "cryptoescrow.eu",
    "cryptohunger.com",
    "cryptonotepool.org.uk",
    "dwarfpool.com",
    "extremepool.com",
    "extremepool.org",
    "hashinvest.net",
    "iwanttoearn.money",
    "maxcoinpool.com",
    "mine.moneropool.org",
    "minemonero.gq",
    "minercircle.com",
    "mining4all.eu",
    "miningpoolhub.com",
    "mixpools.org",
    "mmcpool.com",
    "monero.crypto-pool.fr",
    "monero.cryptopool.fr",
    "monero.farm",
    "monero.hashvault.pro",
    "monero.lindonpool.win",
    "monero.miners.pro",
    "monero.net",
    "monero.riefly.id",
    "monero.us.to",
    "monerohash.com",
    "monerominers.net",
    "moneroocean.stream",
    "moneropool.com",
    "moneropool.com.br",
    "moneropool.nl",
    "moneropool.org",
    "moriaxmr.com",
    "nonce-pool.com",
    "nut2pools.com",
    "opmoner.com",
    "p2poolcoin.com",
    "pool.cryptoescrow.eu",
    "pool.minergate.com",
    "minexmr.com",
    "pool.xmr.pt",
    "pooldd.com",
    "poolto.be",
    "ppxxmr.com",
    "prohash.net",
    "ratchetmining.com",
    "rocketpool.co.uk",
    "sheepman.mine.bz",
    "supportxmr.com",
    "teracycle.net",
    "usxmrpool.com",
    "viaxmr.com",
    "xminingpool.com",
    "xmr.crypto-pool.fr",
    "xmr.hashinvest",
    "xmr.mypool.online",
    "nanopool.org",
    "xmr.prohash.net",
    "xmr.suprnova.cc",
    "xmrpool.de",
    "xmrpool.eu",
    "xmrpool.net",
    "xmrpool.xyz",
    "xmr.pool.minergate.com",
    "greenpool.site",
    "xmr.omine.org",
    "seollar.me",
    "f2pool.com"
]

minerTools = [
    "SRBMiner-MULTI",
    "xmrig",
    "xmr-stak",
    "minerd",   #cpuminer
    "cpuminer",
    "cgminer",
    "bfgminer",
    "minergate-cli",
    "xmr-stak-cpu"
]

class Crawl_thread(threading.Thread):
    def __init__(self, url, path, devops):
        threading.Thread.__init__(self)
        self.baseUrl = url.strip('\n')
        # username/reponame
        self.image = self.baseUrl.split("/")[3] + "/" + self.baseUrl.split("/")[4]
        self.repoDict = self.baseUrl.split("/")[4]
        # git clone self.repoAddress
        self.repoAddress = "https://github.com/" + self.image + ".git"
        # git checkout -b self.checkout
        self.checkout = self.baseUrl.split("/")[6]
        # files in the repos
        self.fileList = []
        #print ("Dockerfile address: ", self.DockerfileAddress)
        self.downloadPath = path + "/"

        self.devops = devops

    def run(self):
        print('Start Download Thread: ', self.image)

        # Downloads github repo
        status = self.download_repo()
        if status == 0:
            print ("Download repo:", self.image, "failed!")
            return

        # Add config file... in fileList
        self.get_repo_fileList()

        # check the config files whether contains mining info
        self.check_repo_configFiles()

    def download_repo(self):
        commands = "cd " + self.downloadPath
        commands = commands + " && /usr/bin/git clone " + self.repoAddress
        commands = commands + " && cd " + self.repoDict
        #commands = commands + " && git checkout -b " + self.checkout

        ret = subprocess.run(commands, shell=True, timeout=60, stderr=subprocess.PIPE)
        # success
        if ret.returncode == 0:
            commands = "cd " + self.downloadPath + "/" + self.repoDict + " && /usr/bin/git checkout -b " + self.checkout
            ret1 = subprocess.run(commands, shell=True, timeout=60, stderr=subprocess.PIPE)
            if ret1 != 0:
                print (ret1.stderr)
            return 1
        # Fail to download repo
        print ("Fail to download repo: ", ret)
        return 0

    def get_repo_fileList(self):
        root = self.downloadPath + self.repoDict
        for root, dirs, files in os.walk(root, topdown=True):
            for name in files:
                # Only needs config file or Dockerfile
                if name.endswith(".yml") or name.endswith(".yaml") or name.endswith(".json") or name.endswith(".sh") or "Dockerfile" in name:
                    self.fileList.append(os.path.join(root, name))

    def check_repo_configFiles(self):
        writeFlag = 0
        repoResults = {}
        repoResults['user'] = self.image.split('/')[0]
        repoResults['repo'] = self.repoDict
        repoResults['filename'] = ""
        #fileResults['filename'] = filePath.rsplit('/',1)[1]
        repoResults['configFile'] = self.devops
        repoResults['githubAddress'] = self.baseUrl

        for filePath in self.fileList:
            file = None
            fileContent = []
            DockerfileFlag = 0

            if filePath.endswith("/Dockerfile"):
                fileContent = resolve_Dockerfile_from_file(filePath)
                if fileContent == None:
                    print ("Dockerfile resolving falied!")
                    continue
                DockerfileFlag = 1
            else:
                file = open(filePath, "r")
                try:
                    fileContent = file.readlines()
                except Exception as e:
                    print ("error:", e, "\nfilepath:", filePath)
                    file.close()
                    continue

                if file != None:
                    file.close()

            # Using regx to get wallet address will have lots of fake reports
            # Checking the wallet address after make sure there exists mining tools or pool address
            walletFlag = 0
            for line in fileContent:
                prefix, pool, wallet, tool = check_minerPools_Tools(line, DockerfileFlag)
                if pool != "" or wallet != "" or tool != "":
                    walletFlag = 1
                    writeFlag = 1

                    filename = filePath.rsplit('/',1)[1]
                    if "filename" in repoResults.keys() and filename != "":
                        repoResults["filename"] = repoResults["filename"] + ";\n" + filename
                    else:
                        repoResults["filename"] = filename

                    if "pool" in repoResults.keys() and pool != "":
                        if pool not in repoResults["pool"]:
                            repoResults["pool"] = repoResults["pool"] + ";\n" + pool
                    else:
                        repoResults["pool"] = pool

                    if "tool" in repoResults.keys() and tool != "":
                        if tool not in repoResults["tool"]:
                            repoResults["tool"] = repoResults["tool"] + ";\n" + tool
                    else:
                        repoResults["tool"] = tool

                    if "prefix" in repoResults.keys() and prefix != "":
                        if prefix not in repoResults["prefix"]:
                            repoResults["prefix"] = repoResults["prefix"] + ";\n" + prefix
                    else:
                        repoResults["prefix"] = prefix
                    """
                    if "command" in fileResults.keys():
                        fileResults["command"] = fileResults["command"] + ";" + line
                    else:
                        fileResults["command"] = line
                    """

            if walletFlag == 1:
                for line in fileContent:
                    wallet = check_minerWallet(line)

                    if "wallet" in repoResults.keys() and wallet != "":
                        repoResults["wallet"] = repoResults["wallet"] + ";\n" + wallet
                    elif wallet != "":
                        repoResults["wallet"] = wallet

        if writeFlag == 1:
            f_csv.writerow(repoResults)

# csv file: user, repo, filename, Dockerfile[prefix], minor command, pools, wallet, tool

def check_minerPools_Tools(line, DockerfileFlag):
    prefix = ""
    tool = ""
    pool = ""
    wallet = ""

    if DockerfileFlag == 1:
        try:
            # prefix is "RUN", "FROM" ...
            prefix = line.split()[0]
        except Exception as e:
            print ("Can't resolving the prefix:", line)
            pass

    for minerTool in minerTools:
        if minerTool in line:
            tool = minerTool

    for minerPool in minerPools:
        if minerPool in line:
            pool = minerPool

    if "-u" in line or "-o" in line:
        items = line.split()
        for index in range(len(items)):
            if items[index] == "-u" and wallet != "":
                try:
                    wallet = items[index+1]
                except Exception as e:
                    pass
            if items[index] == "-o" and pool != "":
                try:
                    pool = items[idex+1]
                except Exception as e:
                    pass

    return prefix, pool, wallet, tool

def check_minerWallet(line):
    wallet = ""

    #wallets = re.search('4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}', line)
    wallets = re.search('4([0-9]|[A-B])(.){93}', line)
    if wallets != None:
        wallet = wallets.group(0)

    return wallet

def resolve_Dockerfile_from_file(path):
    Dockerfile = []

    file = open(path, 'r')
    commands = file.readlines()
    command_string = ""
    for command in commands:
        if command == "":
            continue
        if "FROM" in command or "ENV" in command or "RUN" in command or "CMD" in command or "ENTRYPOINT" in command or "COPY" in command or "ADD" in command:
            if command_string != "":
                Dockerfile.append(command_string)
            command_string = command
        else:
            command_string = command_string + command
    Dockerfile.append(command_string)

    file.close()

    return Dockerfile

header = ["user", "repo", "filename", "configFile", "githubAddress", "pool", "wallet", "tool", "prefix"]
fLog = open('repo_analyze_results.csv','a+')
f_csv = csv.DictWriter(fLog, fieldnames = header)
f_csv.writeheader()

def main():
    #cores = multiprocessing.cpu_count() - 3
    #print ("cores is ", cores)
    cores = 15

    for repoList in repoList_Dockerfile:

        path = "./" + repoList.split('.')[0]
        if not os.path.exists(path):
            os.makedirs(path)

        analyze_thread = []
        repo = open(repoList, "r")
        projects = repo.readlines()
        for project in projects:
            thread = Crawl_thread(project, path, repoList)
            # keep the threads < cores numbers
            if len(threading.enumerate()) < cores:
                thread.start()
                analyze_thread.append(thread)
            else:
                for t in analyze_thread:
                    t.join()

        for t in analyze_thread:
            t.join()

        repo.close()

    fLog.close()

if __name__ == '__main__':
    main()