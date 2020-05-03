import os
import requests
from bs4 import BeautifulSoup
import re
import time

def extract_proxy_url(url):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
    headers = {'User-Agent': user_agent}
    try:
        r = requests.get(url, headers = headers, timeout = 20)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return(r.text)
    except:
        return None

def resolve_proxy_ip(response):
    proxy_ip_list = []
    soup = BeautifulSoup(response, 'html.parser')
    proxy_ips = soup.find(id = 'ip_list').find_all('tr')
    for proxy_ip in proxy_ips:
        if len(proxy_ip.select('td')) >= 8:
            ip = proxy_ip.select('td')[1].text
            port = proxy_ip.select('td')[2].text
            protocol = proxy_ip.select('td')[5].text
            if protocol in ('HTTP','HTTPS','http','https'):
                proxy_ip_list.append(f'{protocol}://{ip}:{port}')
    return proxy_ip_list

def get_proxies():
    proxy_ip_list = []
    if os.path.exists("./valid_proxy_ip.list"):
        with open("./valid_proxy_ip.list", "r") as log:
            for line in log.readlines():
                proxy_ip_list.append(line.strip())
    else:
        proxy_url = 'https://www.xicidaili.com/'
        text = extract_proxy_url(proxy_url)
        if text != None:
            proxy_ip_list = resolve_proxy_ip(text)

    return proxy_ip_list

def open_url_using_proxy(url, proxy):
    headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    proxies = {}
    if proxy.startswith(('HTTPS','https')):
        proxies['https'] = proxy
    else:
        proxies['http'] = proxy

    try:
        r = requests.get(url, headers = headers, proxies = proxies, timeout = 10)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text, r.status_code
    except:
        return "", -200

def open_url_without_proxy(url):
    headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }

    try:
        r = requests.get(url, headers = headers)
        if r.status_code == 200:
            return r.text, r.status_code
        elif r.status_code == 429:
            return "", 429
    except:
        return "", -200

proxy_ip_list = []
proxy_ip_list = get_proxies()

def get_url_use_proxy(url):
    global proxy_ip_list
    if len(proxy_ip_list) == 0:
        proxy_ip_list = get_proxies()

    for proxy in proxy_ip_list:
        text, status = open_url_using_proxy(url, proxy)

        if status == -200:
            continue
        elif status == 429:
            continue
        elif status == 200:
            return text

    text, status = open_url_without_proxy(url)
    while status == 429:
        print ("[WARN] High frequency requests...")
        time.sleep(60)
        text, status = open_url_without_proxy(url)
        if status == 200:
            return text
        else:
            return ""
    return text
