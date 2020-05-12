import requests
import json

'''
-Limitations
* For API requests using Basic Authentication or OAuth, you can make up to 5000 requests per hour.
-Parameters
* token: user token ref: https://developer.github.com/v3/#oauth2-token-sent-in-a-header
* ownerName: user's name
* repoName: repository's name
-Return
* save result into json file
* json file name is ownerName_repoName_commitsPageID
* For example, ownerName_repoName_commitsPage1
'''
def getCommitByPage(token, ownerName, repoName):
    i = 1
    url = "https://api.github.com/repos/" + ownerName + "/" + repoName + "/commits?page=1&per_page=100"
    headers = {"Authorization":"token %s"%token}
    response = requests.get(url, headers=headers)
    headers = response.headers
    data = response.content
    myjson = data.decode("utf-8")
    with open(ownerName + '_' + repoName + 'commits_page1', 'w') as f:
        json.dump(myjson, f)
    while response.status_code == 200 and int(headers['x-ratelimit-remaining']) > 0:
        try:
            link = response.links
            if 'next' in link:
                url = link['next']
            else:
                break
            response = requests.get(url['url'])
            headers = response.headers
            data = response.content
            myjson = data.decode("utf-8")
            i = i + 1
            with open(ownerName + '_' + repoName + '_commits_page%d' % i, 'w') as f:
                json.dump(myjson, f)

        except Exception as e:
            print(e)
            response = requests.get(url)


getCommitByPage("738692d654cf5797766c16a592351ae4e3f430ea","secure-software-engineering", "soot-infoflow-android")
