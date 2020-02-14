import csv
import threading
import subprocess

class push_thread(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.proxy = config[0]
        self.email = config[1]
        self.user = config[2]
        self.passwd = config[3]
        self.repo = config[4]

    def run(self):
        commands = "sudo docker run -it --env HTTP_PROXY=\"{}\" --env HTTPS_PROXY=\"{}\" " \
                   "--env FTP_PROXY=\"{}\" --env http_proxy=\"{}\" --env https_proxy=\"{}\" " \
                   "--env ftp_proxy=\"{}\" --env GIT_ADDRESS=\"{}\" --env GIT_EMAIL=\"{}\" " \
                   "--env GIT_USER=\"{}\" --env GIT_PASS=\"{}\" ubuntu:proxy".format(self.proxy,self.proxy,self.proxy,self.proxy,self.proxy,self.proxy,self.repo,self.email,self.user,self.passwd)

        for i in range(5):
            ret = subprocess.run(commands, shell=True, timeout=60, stderr=subprocess.PIPE)
            # success
            if ret.returncode == 0:
                break
            print ("retry ", i, "times...")

def main():
    cores = 20
    push_thread = []

    csvFile = open("account.csv", "r")
    reader = csv.reader(csvFile)

    for configs in reader:
        thread = push_thread(configs)
        # keep the threads < cores numbers
        if len(threading.enumerate()) < cores:
            thread.start()
            push_thread.append(thread)
        else:
            for t in push_thread:
                t.join()

    for t in push_thread:
        t.join()

    csvFile.close()
