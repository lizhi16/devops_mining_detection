# This script used to get the list of github repo address
# which contains the DevOps platforms' config files
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver

# save path for the list (1. without Docker; 2. contains Dockerfile)
Path = "./repoList_{}.txt"

address = "https://github.com/search?p={}&q=size%3A{}..{}+filename%3A{}&type=Code"

configFiles = {
    "Dockerfile": "Dockerfile",
}

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

    cookie = driver.get_cookies()
    driver.quit()

    ck = requests.cookies.RequestsCookieJar()
    #add cookie to CookieJar
    for i in cookie:
        ck.set(i["name"], i["value"])
    #update cookie in session
    session.cookies.update(ck)

def resolve_suspect_github_list(savePath, startSize, endSize, configFile):
    projectList = open(savePath, "a+")

    count = 0

    index = 1
    totalPage = 100
    while index <= totalPage:
        url = address.format(str(index), startSize, endSize, configFile)
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

            projectConfig = str(project['title'])
            if "/" in projectConfig:
                projectConfig = projectConfig.rsplit("/",1)[1]

            if projectConfig == "Dockerfile":
                count = count + 1
                print ("Get Dockerfile ->", count)

                Url = str(project['href']).split("/")
                projectUrl = "https://github.com/" + Url[1] + "/" + Url[2] + "/tree/" + Url[4]
                projectList.write(projectUrl + "\n")

        if content.status_code == 429:
            index = index - 1
            print ("We get the 429, sleeping 60s")
            time.sleep(60)

        index = index + 1

    projectList.close()

def check_search_results_numbers(startSize, endSize, configFile):
    url = address.format("1", startSize, endSize, configFile)

    content = session.get(url)
    soup = BeautifulSoup(content.text,'html.parser')

    links = soup.find_all('span',class_="v-align-middle")
    for link in links:
        # "Showing *** available code results" means useful info
        if "code results" in link.text:
            number = str(link.text).split()[1]
            # if results over 1000, it will show "1,000"
            if "," in number:
                return -1
            else:
                print ("the number of results is", int(number))
                return int(number)
        elif "We couldn’t find any code matching" in link.text:
                return -2

    links = soup.find_all('div',class_="px-2")
    for link in links:
        if "code results" in link.text:
            number = str(link.text).split()[0]
            # if results over 1000, it will show "1,000"
            if "," in number:
                return -1
            else:
                print ("the number of results is", int(number))
                return int(number)
        elif "We couldn’t find any code matching" in link.text:
            return -2
       
    links = soup.find_all('h3')
    for link in links:
        if "code results" in link.text:
            number = str(link.text).split()[0]
            # if results over 1000, it will show "1,000"
            if "," in number:
                return -1
            else:
                print ("the number of results is", int(number))
                return int(number)
        elif "We couldn’t find any code matching" in link.text:
            return -2

    return -3

def main():
    # login
    login("ccs202003@protonmail.com", "Lizhiccs202003")

    stopFlag = 1000000000
    for devops, configFile in configFiles.items():
        savePath = Path.format(devops)

        startSize = 1
        step = 100
        endSize = startSize + step

        # The times using to retry
        tryFlag = 5
        while endSize <= stopFlag:
            ok = check_search_results_numbers(startSize, endSize, configFile)
            if ok > 0:
                resolve_suspect_github_list(savePath, startSize, endSize, configFile)
                startSize = endSize + 1
                endSize = startSize + step
                tryFlag = 5
            elif ok == -1:
                # Github can receive the float type in searching
                step = step/2
                endSize = startSize + step
                tryFlag = 5
                continue
            # maybe in [..., ...] doesn't have results, and [..+1000, ...+2000] has results
            elif ok == -2:
                endSize = startSize + step * 2
                tryFlag = 5
                continue
            elif ok == -3:
                print ("Can't get correct results' number!")
                if tryFlag <= 0:
                    break
                tryFlag = tryFlag - 1
                print ("Preparing to retry...")
                time.sleep(10)
                continue

if __name__ == '__main__':
    main()
    driver.quit()
