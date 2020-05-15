import time
import requests
import threading

basePath = "./results/"

keywords = [
    # tools
    "xmrig",
    "minerd",
    "cpuminer",
    "xmr-stak-cpu",
    # wallet
    "fewa342rwr",
    "jerolamo",
    "empireofbooks",
    "brahim7",
    "keshavarziamir8",
    "4BrL51JCc9NGQ71kWhnYoDRffsDZy7m1HUU7MRU4nUMXAHNFBEJhkTZV9HdaL4gfuNBxLPc3BeMkLGaPbF5vWtANQpLT6dWELSeGhybhEC",
    "41jcJH1B2Hj1vGJGioERFGi71Gu3AniSmC75kQReMikC8wB9rkTeguQ9DPiUYRNp4K5ucDrv34vWN7yEYkLmWD6NGq8vXqA",
    "47w6Lu6kG3jNDyRLHviQeAjmGPPHkHbgBYBaavP2rVpahLQqrW8WcVh2m5cjhmVq7VAkXW1bDjEuzbNNBj43tRfGGwZsDhT",
    "41jcJH1B2Hj1vGJGioERFGi71Gu3AniSmC75kQReMikC8wB9rkTeguQ9DPiUYRNp4K5ucDrv34vWN7yEYkLmWD6NGq8vXqA",
    "489SKk43bDUL3KF3E5RPMmEVpB6cLYJJcWZmPbmxrJ1vGyh3dAADeLxUQK8UK6yqNWTJG96cATyiG7Qs39PXi6K932ug3zS",
    "45UVbdyweuJV5peeuD1ypVbFs6Z1nYhRB4r9BEL9xYjE8Ej8Pjob3LQX2dN4m314gB87Z1M9TbabwN4g4L9184dcCLyiU6y",
    # devops
    ".gitlab-ci.yml",
    "bitrise.yml",
    ".platform.app.yaml",
    "solano.yml",
    "wercker.yml",
    "buddy.yml",
    "shippable.yml",
    ".cirrus.yml",
    "appveyor.yml",
    "codeship-steps.yml",
    ".travis.yml",
    ".cirrus.yml",
    "codefresh.yml",
    "azure-pipelines.yml",
    "circleci",
    ".scrutinizer.yml",
    "Dockerfile",
]

def get_proxy():
    return requests.get("http://18.236.149.174:5010/get/").json()

def delete_proxy(proxy):
    requests.get("http://18.236.149.174:5010/delete/?proxy={}".format(proxy))

def getHtml(url):
    retry_count = 10
    while retry_count > 0:
        proxy = get_proxy().get("proxy")
        try:
            content = requests.get(url, proxies={"http": "http://{}".format(proxy)})
            if content.status_code == 429:
                print ("[WARN] High frequency requests...")
                time.sleep(60)
                retry_count -= 1
            elif content.status_code == 200:
                return content.text

        except Exception:
            retry_count -= 1

    delete_proxy(proxy)
    return None

class Crawl_thread(threading.Thread):
    def __init__(self, address, id):
        threading.Thread.__init__(self)
        # base info
        self.project_id = id
        self.address = address

        # target url
        self.url = ""

        # url content
        self.content = ""

    def run(self):
        print('Start resolve project Thread: ', self.project_id)

        for keyword in keywords:
            print ("keyword:", keyword)
            # initialize url
            self.url = self.address.format(keyword = keyword, project_id = self.project_id)

            # get content of the url
            if self.get_url() == 0:
                return

            # resolve the content
            state = self.resolve_content()

            # the project id is illegal
            if state == -1:
                print ("[WARN] project id:", self.project_id, " is illegal...")
                with open(basePath + "illegal_project_id.list", "a+") as log:
                    log.write(self.project_id + "\n")
                return
            elif state == 1:
                with open(basePath + "suspect_project_url.list", "a+") as log:
                    log.write(self.url + "\n")

    def get_url(self):
        self.content = getHtml(self.url)
        if self.content == None:
            return 0
        return 1

    def resolve_content(self):
        if self.content == "":
            return 0

        # the project exists and get results
        if "Showing" in self.content and "code result" in self.content:
            return 1
        # the project exists and doesn't have results
        elif "We couldn't find any code results matching" in self.content:
            return 2
        # the project doesn't exist
        else:
            return -1

def search_keywords_gitlab():
    project_id_start = 10000000
    project_id_end = 10010000
    #project_id_end = 20000000
    url = "https://gitlab.com/search?utf8=%E2%9C%93&search={keyword}&group_id=&project_id={project_id}&search_code=true&repository_ref=master&nav_source=navbar#"

    cores = 48
    analyze_thread = []
    for id in range(project_id_start, project_id_end):
        thread = Crawl_thread(url, str(id))

        # keep the threads < cores numbers
        if len(threading.enumerate()) <= cores:
            thread.start()
            analyze_thread.append(thread)
        else:
            for t in analyze_thread:
                t.join()

    for t in analyze_thread:
        t.join()

if __name__ == '__main__':
    search_keywords_gitlab()
