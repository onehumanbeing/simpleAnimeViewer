#coding:utf8
import json
import os
import traceback

from .ua import get_header_with_rnd_ua, get_header_with_desktop_rnd_ua

from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
host = os.getenv("HOST")

@app.route('/tag', methods=['POST', 'GET'])
def tag():
    data = request.args
    search_data = data.get('v', None)
    if not search_data:
        return jsonify([])
    else:
        return jsonify(get_tag_from_name(search_data))


@app.route('/show', methods=['POST', 'GET'])
def show():
    data = request.args
    search_data = data.get('v', None)
    if not search_data:
        return jsonify({"success": 0, "err": "v"})
    else:
        return jsonify(get_video_data_from_url(search_data))


@app.route('/search', methods=['POST', 'GET'])
def search():
    data = request.args
    search_data = data.get('v', None)
    if not search_data:
        return jsonify([])
    else:
        return jsonify(get_search_data(search_data)), 200


def get_video_data_from_url(url):
    try:
        s = requests.Session()
        s.headers.update(get_header_with_desktop_rnd_ua())
        res = s.get(
            url=url,
            timeout=5,
        )
        if res.status_code != 200:
            print(res.text)
            print(res.status_code)
            return {"success": 0, "err": res.text}
        soup = BeautifulSoup(res.text)
        player_data = soup.find_all('script')[5]
        player_url = host + player_data.get("src")
        print("player_url: " + player_url)
        
        cms_player_res = s.get(
            url=player_url,
            timeout=5,
        )
        p = cms_player_res.text
        pp = p[p.find("var cms_player = ") + len("var cms_player = "):p.rfind("document.write")-1]
        a = json.loads(pp)
        video_player_url = str(a['url']) + "&" + "auth_key=" + str(a['auth_key']) + "&" + "time=" + str(a['time'])
        print("video_player_url: " + video_player_url)
        video_player_res = s.get(
            url=video_player_url,
            timeout=5,
        )
        dd = video_player_res.text
        res_url = dd[dd.find("url: \"https:") + 6:dd.find("pic:")].replace('\",\n', '').replace(' ', '')
        return {"success":1, "msg": res_url}
    except:
        print("GET player failed")
        e = traceback.format_exc()
        print(e)
        return {"success":0, "err": e}


def get_search_data(search_data):
    try:
        res_data = []
        url = host + "/video/search/" + str(search_data) + ".html"
        res = requests.get(
            url=url,
            headers=get_header_with_rnd_ua(),
            timeout=5,
        )
        if res.status_code != 200:
            print(res.text)
            print(res.status_code)
            return ["Error"]
        soup = BeautifulSoup(res.text)
        main_container = soup.find(class_="container ff-bg")
        print(main_container.ul.contents)
        for item in main_container.ul.contents:
            if len(item) <= 4:
                continue  # \n
            res_data.append(item.h2.a.get("title"))
        return res_data
    except:
        print(host+"/video/search failed")
        print(traceback.format_exc())
        return ["Error"]

def get_tags_from_url(url=host+"/video/detail/52134.html"):
    try:
        res_data = list()
        header = get_header_with_rnd_ua()
        res = requests.get(
            url=url,
            headers=header,
            timeout=5,
        )
        if res.status_code != 200:
            print(res.text)
            print(res.status_code)
            return []
        soup = BeautifulSoup(res.text)
        index = 0
        find_index = False
        print(soup.find(class_="nav nav-tabs ff-playurl-tab"))
        for item in soup.find(class_="nav nav-tabs ff-playurl-tab").contents:
            if len(str(item)) <= 4:
                print("continue item")
                print(len(str(item)))
                print(item)
                continue  # \n
            content = str(item.a)
            if content.find("天国") != -1:
                find_index = True
                break
            index += 1
        if not find_index:
            print("not find index")
            index = 0
        print("index %d" % index)
        inner = dict()
        tag_list = soup.find_all(class_="btn btn-default btn-block btn-sm ff-text-hidden")
        for item in tag_list:
            if item.string in inner:
                break
            inner.setdefault(item.string, 0)
            if item.string.find("提取") != -1:
                continue
            if str(item.get('href')).find("pan.baidu") != -1:
                continue
            r = str(item.get('href'))
            href_head = r[:r.find("-")+1]
            href_tail = r[r.rfind("-"):]
            href_result = href_head + str(index+1) + href_tail
            res_data.append({
                "s": item.string,
                "d": host + href_result
            })
        return res_data
    except:
        print("GET %s/video/detail failed" % host)
        print(traceback.format_exc())
        return []


def get_tag_from_name(data):
    try:
        res_data = None
        url = host + "/video/search/" + str(data) + ".html"
        res = requests.get(
            url=url,
            headers=get_header_with_rnd_ua(),
            timeout=5,
        )
        if res.status_code != 200:
            print(res.text)
            print(res.status_code)
            return ["Error"]
        soup = BeautifulSoup(res.text)
        main_container = soup.find(class_="container ff-bg")
        # print(main_container.ul.contents)
        for item in main_container.ul.contents:
            if len(item) <= 4:
                continue  # \n
            res_data = host + item.h2.a.get("href")
            print(res_data)
            break
        if not res_data:
            assert False
        return get_tags_from_url(res_data)
    except:
        print(host+"video/search failed")
        print(traceback.format_exc())
        return ["Error"]


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=9090, debug=True)
