# This script used to get the list of github repo address
# which contains the DevOps platforms' config files
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver

# save path for the list (1. without Docker; 2. contains Dockerfile)
Path = "./repoList_{}.txt"
Path_Dockerfile = "./repoList_{}_Dockerfile.txt"
address = "https://github.com/search?p={}&q=size%3A{}..{}+path%3A%2F+filename%3A{}&type=Code"
address_circleci = "https://github.com/search?p={}&q=size%3A{}..{}+path%3A%2F.circleci%2F+filename%3A{}&type=Code"

configFiles = {
    "azure": "azure-pipelines.yml",
    "gitlab": ".gitlab-ci.yml",
    "appveyor": "appveyor.yml",
    "codeship":"codeship-steps.yml",
    "travis": ".travis.yml",
    "cirrus": ".cirrus.yml"
    "codefresh":"codefresh.yml",
    "bitrise": "bitrise.yml",
    "circleci": "config.yml"
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

def resolve_suspect_github_list(savePath, savePath_Dockerfile, startSize, endSize, configFile):
    projectList = open(savePath, "a+")
    projectList_Dockerfile = open(savePath_Dockerfile, "a+")

    index = 1
    totalPage = 100
    while index <= totalPage:
        url = ""
        if configFile == "config.yml":
            url = address_circleci.format(str(index), startSize, endSize, configFile)
        else:
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
            if configFile == "config.yml":
                projectConfig = projectConfig.split('/')[1]

            Url = str(project['href']).split("/")
            projectUrl = "https://github.com/" + Url[1] + "/" + Url[2] + "/tree/" + Url[4]

            flag = filter_Dockerfile(projectConfig, projectUrl, configFile)
            # Only containing config files, doesn't contain Dockerfile
            if flag == 1:
                projectList.write(projectUrl + "\n")
            # Containing config file and Dockerfile
            elif flag == 2:
                projectList_Dockerfile.write(projectUrl + "\n")

        if content.status_code == 429:
            index = index - 1
            print ("We get the 429, sleeping 60s")
            time.sleep(60)

        index = index + 1

    projectList.close()
    projectList_Dockerfile.close()

    return project

def filter_Dockerfile(config, url, configFile):
    if config != configFile:
        print("config is not match configFile",config, configFile)
        return 0

    if check_Dockerfile_in_github(url):
        # Contains Dockerfile
        return 2
    else:
        # Doesn't contains Dockerfile
        return 1

def check_Dockerfile_in_github(githubAddress):
    print ("Checking Dockerfile in github...")

    if Check_github_exist(githubAddress) == 0:
        print (githubAddress, " doesn't exist...")
        return 0

    url = githubAddress
    headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    content = requests.get(url,headers=headers)

    soup = BeautifulSoup(content.text,'html.parser')
    links = soup.find_all('tr',class_="js-navigation-item")
    for link in links:
        try:
            fileType = link.find('svg')['aria-label']
            fileName = link.find('a', class_="js-navigation-open")['title']
            if fileType == "file" and fileName == "Dockerfile":
                return 1
        except Exception as e:
            print("error: ", link)
            continue

    return 0

def Check_github_exist(github):
    headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    for i in range(11):
        content = requests.get(github,headers=headers)
        if content.status_code == 200:
            return 1
        else:
            continue
    return 0

def check_search_results_numbers(startSize, endSize, configFile):
    url = ""
    if configFile == "config.yml":
        url = address_circleci.format("1", startSize, endSize, configFile)
    else:
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
        savePath_Dockerfile= Path_Dockerfile.format(devops)

        startSize = 1
        step = 100
        endSize = startSize + step

        # The times using to retry
        tryFlag = 5
        while endSize <= stopFlag:
            ok = check_search_results_numbers(startSize, endSize, configFile)
            if ok > 0:
                resolve_suspect_github_list(savePath, savePath_Dockerfile, startSize, endSize, configFile)
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
