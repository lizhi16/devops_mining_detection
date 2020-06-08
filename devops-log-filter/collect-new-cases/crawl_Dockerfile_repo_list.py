# This script used to get the list of github repo address
# which contains the DevOps platforms' config files
import requests
import time
import json
import sys
from bs4 import BeautifulSoup
from selenium import webdriver

# save path for the list (1. without Docker; 2. contains Dockerfile)
Path = "./repoList_circleci-new-cases.txt"
address = "https://github.com/search?p={}&q=caesra01&type=Code"

#driver = webdriver.Firefox(executable_path = "/N/u/zli10/Carbonate/malicious_dockerfile/bin/geckodriver")
driver = webdriver.Firefox()
driver.maximize_window()
session = requests.session()
def login(account, password):
    global driver, session
    driver.get('https://github.com/login')
    time.sleep(2)
    driver.find_element_by_id('login_field').send_keys(account)
    driver.find_element_by_id('password').send_keys(password)
    driver.find_element_by_xpath('//input[@class="btn btn-primary btn-block"]').click()

    time.sleep(20)

    cookie = driver.get_cookies()
    driver.quit()

    ck = requests.cookies.RequestsCookieJar()
    #add cookie to CookieJar
    for i in cookie:
        ck.set(i["name"], i["value"])
    #update cookie in session
    session.cookies.update(ck)

def resolve_suspect_github_list(savePath, startSize, endSize):
    projectList = open(savePath, "a+")

    index = 1
    totalPage = 100
    while index <= totalPage:
        #url = address.format(str(index))
        #url = address.format(str(index), startSize, endSize)
        print ("Index-", index, ": ", url)

        content = session.get(url)
        soup = BeautifulSoup(content.text,'html.parser')

        if index == 1:
            # Get correct total page numbers from reqeusts
            try:
                totalPage = int(soup.find('em', class_="current")['data-total-pages'])
            except Exception as e:
                print ("Can't get the total pages!")
                totalPage = 1
                #return None

        links = soup.find_all('div',class_="f4 text-normal")
        for link in links:
            project = link.find('a')

            projectConfig = str(project['title'].encode("utf-8"))
            if "/" in projectConfig:
                projectConfig = projectConfig.rsplit("/",1)[1]


            Url = str(project['data-hydro-click'])
            config = json.loads(Url)
            try:
                repoUrl = config['payload']['result']['url']
                projectList.write(repoUrl + "\n")
            except:
                with open("cannot-resolve_repo.list", "a+") as log:
                    err = str(project['href']).split("/")
                    projectUrl = "https://github.com/" + err[1] + "/" + err[2] + "/tree/" + err[4]
                    log.write(projectUrl + "\n")

        if content.status_code == 429:
            index = index - 1
            print ("We get the 429, sleeping 60s")
            time.sleep(60)

        index = index + 1
        time.sleep(3)

    projectList.close()

def check_search_results_numbers(startSize, endSize):
    url = address.format("1", startSize, endSize)

    content = session.get(url)
    soup = BeautifulSoup(content.text,'html.parser')

    links = soup.find_all('span',class_="v-align-middle")
    for link in links:
        # "Showing *** available code results" means useful info
        if "code results" in link.text:
            number = str(link.text).split()[1]
            # if results over 1000, it will show "1,000"
            if "," in number:
                if float(endSize) - float(startSize) <= 0.01:
                    return 1
                return -1
            else:
                print ("the number of results is", int(number))
                return int(number)
        elif "We couldn't find any code matching" in link.text:
                return -2

    links = soup.find_all('div',class_="px-2")
    for link in links:
        if "code results" in link.text:
            number = str(link.text.encode('utf-8')).split()[0]
            # if results over 1000, it will show "1,000"
            if "," in number:
                if float(endSize) - float(startSize) <= 0.1:
                    return 1
                return -1
            else:
                print ("the number of results is", int(number))
                return int(number)
        elif "We couldnt find any code matching" in link.text:
            return -2

    print("url is", url)
    return -3

def main():
    # login
    login("ccs2021001@protonmail.com", "Lizhi906096237")

    #stopFlag = 1000000000
    #stopFlag = int(sys.argv[2])
    stopFlag = 1500
    for devops, configFile in configFiles.items():
        #savePath = Path.format(devops)
        savePath = Path

        #startSize = int(sys.argv[1])
        # 115,166
        startSize = 1340
        step = 100
        endSize = startSize + step

        resolve_suspect_github_list(savePath, 1, 100)
        
        # The times using to retry
        """
        tryFlag = 5
        while startSize <= stopFlag:
            print ("start in while", startSize, step, endSize)
            ok = check_search_results_numbers(startSize, endSize)
            if ok > 0:
                resolve_suspect_github_list(savePath, startSize, endSize)
                startSize = endSize + 1
                endSize = startSize + step
                tryFlag = 5
            elif ok == -1:
                # Github can receive the float type in searching
                if endSize - startSize == 0:
                    endSize = endSize + 0.01
                elif endSize - startSize <= 1:
                    endSize = startSize + (endSize - startSize)/2
                else:
                    step = step/2
                    endSize = startSize + step
                tryFlag = 5
                continue
            # maybe in [..., ...] doesn't have results, and [..+1000, ...+2000] has results
            elif ok == -2:
                if endSize - startSize <= 1:
                    step = (endSize - startSize)/2 + 0.1
                elif endSize - startSize > 100:
                    step = 100
                startSize = endSize
                endSize = startSize + step
                tryFlag = 5
                continue
            elif ok == -3:
                print ("Can't get correct results' number!")
                if tryFlag <= 0:
                    startSize = endSize
                    endSize = startSize + step
                    continue
                tryFlag = tryFlag - 1
                print ("Preparing to retry...")
                time.sleep(10)
                continue
        """

if __name__ == '__main__':
    main()
    driver.quit()
