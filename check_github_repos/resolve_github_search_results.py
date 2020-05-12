import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from malicious_behavior_policies import minerTools
from malicious_behavior_policies import minerPools

basePath = "./results/"
configFiles = [
    #".gitlab-ci.yml",
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
]

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

    # github maybe need verified code
    # time.sleep(20)

    cookie = driver.get_cookies()
    driver.quit()

    ck = requests.cookies.RequestsCookieJar()
    #add cookie to CookieJar
    for i in cookie:
        ck.set(i["name"], i["value"])
    #update cookie in session
    session.cookies.update(ck)

def get_url_content(url):
    content = session.get(url)
    # WARN: for high frequency requests
    while content.status_code == 429:
        print("[WARN] High frequncy requests!")
        time.sleep(60)
        content = session.get(url)

    if content.status_code == 200:
        return content
    else:
        print ("[ERROR] Can't resolve url:", url)
        return None

def resolve_search_list(url):
    # repolist info
    repoList = []
    count = 0
    # default config
    index = 1
    totalPage = 100
    while index <= totalPage:
        url = url.format(page = str(index))
        print ("Index-", index, ": ", url)

        content = get_url_content(url)
        if content == None:
            return None
        soup = BeautifulSoup(content.text,'html.parser')

        if index == 1:
            # Get correct total page numbers from reqeusts
            try:
                totalPage = int(soup.find('em', class_="current")['data-total-pages'])
            except Exception as e:
                totalPage = 1

        links = soup.find_all('div',class_="f4 text-normal")
        for link in links:
            count = count + 1
            print ("Get Repos ->", count)

            project = link.find('a')
            address = str(project['data-hydro-click'])
            config = json.loads(address)
            try:
                repoUrl = config['payload']['result']['url']
                repoList.append(repoUrl)
            except:
                with open(basePath + "cannot-resolve-repos.list", "a+") as log:
                    err = str(project['href'])
                    log.write(err + "\n")

        index = index + 1
        time.sleep(3)

    return repoList

def check_search_results_numbers(content):
    soup = BeautifulSoup(content.text,'html.parser')

    links = soup.find_all('span',class_="v-align-middle")
    if len(links) == 0:
        links = soup.find_all('div',class_="px-2")

    for link in links:
        # "Showing *** available code results" means useful info
        if "code results" in link.text:
            number = str(link.text).split()[1]
            # if results over 1000, it will show "1,000"
            if "," in number:
                return int(''.join(number.split(",")))
            else:
                return int(number)
        elif "We couldn't find any code matching" in link.text:
            return -1

    return -2

# usually, the github just return max 1000 results
# but lots of times, the results may over the 1000
# we can use the "file size" to control the number of return results
def search_repos_with_filesize(url, startFlag, stopFlag, step):
    startSize = startFlag
    endSize = startSize + step

    reposList = []
    # The times using to retry
    tryFlag = 5
    while endSize <= stopFlag:
        print ("start in while", startSize, step, endSize)
        address = url.format(page = "1", start = str(startSize), end = str(endSize))
        content = get_url_content(address)
        ok = check_search_results_numbers(content)
        if ok > 0 and ok <= 1000:
            reposList.extend(resolve_search_list(address.replace("p=1", "p={page}")))
            #if ok < 50 and step < 1:
            #    step = step * 2
            startSize = endSize
            endSize = startSize + step
            tryFlag = 5
        elif ok > 1000:
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
        # maybe in [..., ...] doesn't have results, and [..+1000, ...+1000] has results
        elif ok == -1:
            if endSize - startSize <= 1:
                step = (endSize - startSize)/2 + 0.1
            elif endSize - startSize > 100:
                step = 100
            startSize = endSize
            endSize = startSize + step
            tryFlag = 5
            continue
        elif ok == -2:
            print ("[WARN] Can't get correct results' number!")
            if tryFlag <= 0:
                startSize = endSize
                endSize = startSize + step
                continue
            tryFlag = tryFlag - 1
            print ("Preparing to retry...")
            time.sleep(10)
            continue

    return reposList

def get_results_date(content):
    indexed = []
    new_flag = 0
    for line in content.text.split("\n"):
        if "Last indexed" in line:
            # Last indexed <relative-time datetime="2019-07-24T07:07:30Z" class="no-wrap">Jul 24, 2019</relative-time>
            indexed.append(line.split("\"")[1])
            if "2020" in line.split("\"")[1]:
                new_flag = 1

    return indexed, new_flag

def search_keywords():
    log_2020 = open(basePath + "contain_miner_info_in_devops_2020" + ".list", "a+")
    log = open(basePath + "contain_miner_info_in_devops" + ".list", "a+")

    url = "https://github.com/search?o=desc&p={page}&q={info}+filename%3A{filename}&s=indexed&type=Code"
    minerInfo = []
    minerInfo.extend(minerTools)
    minerInfo.extend(minerPools)

    for file in configFiles:
        for info in minerInfo:
            print("[INFO] Search for:", file, info)

            address = url.format(page = "1", info = info, filename = file)
            content = get_url_content(url)
            if content == None:
                print ("[ERROR] Can't get the url:", address)
                continue

            if check_search_results_numbers(content) <= 0:
                continue

            date_list, new_flag = get_results_date(content)
            if new_flag == 1:
                log_2020.write(url + "\n")
            elif len(date_list) != 0:
                log.write(url + "\n")

    log_2020.close()
    log.close()

def main():
    # login
    login("ccs202003@protonmail.com", "Lizhiccs202003")
    search_keywords()
    
if __name__ == '__main__':
    main()
    driver.quit()
