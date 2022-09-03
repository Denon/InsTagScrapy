import requests
import json
import urllib.parse as url_parse
import time
import csv

MEDIA_INFO_URL = "https://i.instagram.com/api/v1/media/2880828439776049722/info/"
TAG_INFO_URL = "https://www.instagram.com/graphql/query/?query_hash=ded47faa9a1aaded10161a2ff32abb6b&variables={}"
headers = {'User-Agent':'Instagram 76.0.0.15.395 Android (24/7.0; 640dpi; 1440x2560; samsung; SM-G930F; herolte; samsungexynos8890; en_US; 138226743)'}


def get_cookies_from_file():
    """
    See README about how to get your cookie
    """
    with open('ins_cookie.txt') as f:
        cookie_str_list = f.read().split(";")
        cookies = {}
        for c in cookie_str_list:
            cookie_name = c.split("=")[0]
            cookie_value = c.split("=")[1]
            cookies[cookie_name] = cookie_value

    return cookies


def get_cookies(**kwargs):
    cookies = get_cookies_from_file()
    return cookies


def load_proxy():
    """
    See README about how to set proxy if you need
    """
    try:
        f = open('./config.json')
        proxies = json.loads(f.read())
    except:
        print("No config.")
        proxies = None
    print("PROXIES: {}".format(proxies))
    return proxies


def scrapy_instagram(hashtag, amount):
    s = requests.Session()
    proxies = load_proxy()
    if proxies is not None and proxies['http']:
        s.proxies = proxies
    variables = {
        "tag_name":  hashtag,
        "first": 20,
        "end": ""
    }
    total_count = 0
    total_like = 0
    total_comment = 0
    hot_post_info = None
    tag_info = None
    result = []
    print("crawling, please wait")
    while total_count < amount:
        url_variables = url_parse.quote(json.dumps(variables))
        url = TAG_INFO_URL.format(url_variables)
        response = s.get(url, headers=headers, cookies=get_cookies())
        json_response = response.json()
        if tag_info is None:
            tag_info = {
                'total_post': json_response['data']['hashtag']['edge_hashtag_to_media']['count']
            }
        if hot_post_info is None:
            hot_post_info = json_response['data']['hashtag']['edge_hashtag_to_top_posts']

        for edge in json_response['data']['hashtag']['edge_hashtag_to_media']['edges']:
            total_count += 1
            total_like += edge['node']['edge_liked_by']['count']
            total_comment += edge['node']['edge_media_to_comment']['count']
            result.append([
                edge['node']['id'],
                edge['node']['taken_at_timestamp'],
                repr(edge['node']['edge_media_to_caption']['edges'][0]['node']['text']),
                edge['node']['edge_liked_by']['count'],
                edge['node']['edge_media_to_comment']['count'],
                edge['node']['display_url']
            ])
        if not json_response['data']['hashtag']['edge_hashtag_to_media']['page_info']['has_next_page']:
            break
        variables['end'] = json_response['data']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor']
        time.sleep(0.2)

    save_to_csv(result)
    print("\nsuccess, check result.csv")
    print("tag name: {}".format(hashtag))
    print("total {} posts under this tag".format(tag_info['total_post']))
    print("spider:{} post，avg like:{:.2f}，avg comment:{:.2f}".format(total_count, total_like * 1.0 / total_count,
                                                                     total_comment * 1.0 / total_count))


def save_to_csv(rows):
    """
    save spider result to sqlite db
    :return:
    """
    fields = ['id', 'create_timestamp', 'desc', 'like', 'comment', 'img_url']
    with open("./result.csv", 'w', newline='', encoding='utf-8') as f:
        write = csv.writer(f, delimiter=',')
        write.writerow(fields)
        write.writerows(rows)
    return None


if __name__ == '__main__':
    tag_name = input("input tag name: ")
    amount = input("input scrape amount(at least 60): ")
    scrapy_instagram(tag_name, int(amount))
    input("press any key to exit")
