'''
Created on 2019/12/19

@author: nishidayuki
'''

### GoogleMapスクレイピング
# 使用方法
'''
・Python3のバージョン
>Python 3.7.4
・外部ライブラリのインストール
>Selenium
>BeautifulSoup
>tqdm
・pathの''の中に、空のcsvファイルのパス名を入力する
'''

# モジュールのインポート
from selenium import webdriver # 外部
import time
from bs4 import BeautifulSoup as BS # 外部
import re
import csv
import requests
from tqdm import tqdm # 外部

# クロームのドライバーを用意
driver = webdriver.Chrome()

# クロームドライバーが「GoogleMap」urlを取得・開く
url = 'https://www.google.co.jp/maps/'
driver.get(url)

# time.sleepは、ロード中の処理でエラーが起こらないように、処理を待機させるために使用
time.sleep(3)

# 検索欄にキーワードを入力
keys1 = '郵便番号'
keys2 = input('郵便番号を入力(例 6308113)>')

# データ入力
building_search_id = driver.find_element_by_id("searchboxinput")
building_search_id.send_keys(keys1, keys2) # 検索欄に、keysにインプットされた要素を代入

time.sleep(4)

# クリック
search_button = driver.find_element_by_xpath("//*[@id='searchbox-searchbutton']")
search_button.click()

time.sleep(6)

# 「付近を検索」をクリック
near_search_button = driver.find_element_by_xpath("//*[@id='pane']/div/div[1]/div/div/div[5]/div[3]/div/button")
near_search_button.click()

time.sleep(6)

# 「付近のビル」と入力
building_search_id = driver.find_element_by_id("searchboxinput")
building_search_id.send_keys('付近のビル')

time.sleep(4)

# 「付近のビル」と入力し終わった後の検索蘭をクリック
search_button2 = driver.find_element_by_xpath("//*[@id='searchbox-searchbutton']")
search_button2.click()

time.sleep(7)

## リンクを順にクリックするループ処理
while True:
    try:
        ## リンク数解析
        link_list = []
        page_source = driver.page_source # htmk解析
        soup = BS(page_source, 'html.parser')
        link_text = soup.find(class_ = 'n7lv7yjyC35__left') # スクレイピング
        link_list.append(link_text.text.strip())

        # スクレイピングした文字を一個一個分解する処理(n_gramを使用)
        def n_gram(target, n):
            result = []
            for i in range(0, len(target) - n + 1):
                result.append(target[i : i + n])
            return result

        for i in link_list:
            target = i

        result = n_gram(target, 1) # 1文字ごとに分解してリストに収納したリスト

        # 検索結果が100件超えた時の処理が必要になるかもしれないので、後に実装。(東京でさえ50件超えないので、いらないかも)
        if result[0] == '1':
            link1 = int(result[0])
            link2_s = result[2:4]
            link2 = int("".join(link2_s))
        elif result[2] == '〜':
            link1_s = result[0:2]
            link1 = int("".join(link1_s))
            link2_s = result[3:5]
            link2 = int("".join(link2_s))
        else:
            pass

        ## 使用する空のリストをここに設置
        title_list = [] # スクレイピング要素がないリンクを飛ばすためのリスト
        all_list = [] # csv書き込み用のリスト

        # 検索結果のxpathというものでループを回しています
        path_front = '//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]/div['
        count = 1
        path_end = ']'

        roop_counter = 1 # ループを強制終了させるためのカウンター

        while roop_counter <= link2 - link1 + 1: # リンクを順にクリックさせています
            path = path_front + str(count) + path_end
            l = driver.find_element_by_xpath(path)
            l.click()
            time.sleep(4)

            ## ここからスクレイピング処理-----------------------------------------------------------------------------------
            if count == 1 or 3: # HTML解析
                page_source = driver.page_source
                soup = BS(page_source, 'html.parser')

            # 例外ページをスキップ
            title = soup.find(class_ = 'section-hero-header-title-title GLOBAL__gm2-headline-5')
            title_list.append(title.text.strip())
            title_list_del = title_list.pop()

            if '-' not in title_list_del:
                pass
            else: # 関係ないページはここでスキップ
                count += 2
                roop_counter += 1
                back_button = driver.find_element_by_xpath('//*[@id="pane"]/div/div[1]/div/div/button/span')
                back_button.click()
                time.sleep(5)
                continue

            # スクレイピングの準備
            address = soup.find_all(class_ = 'section-info-text') # 郵便番号・都道府県・市区町村・町名・番地・ビル名

            # 郵便番号をスクレイピングする処理
            target = address[0].text.strip()
            address_result_old = n_gram(target, 1) # 分解した後のリスト
            address_result = [i for i in address_result_old if i != ' '] # 空白を除去したリスト
            postal_code_list = address_result[0:9]
            postal_code = "".join(postal_code_list) # 郵便番号が完成

            # スクレイピング情報の有無を判定
            def Judgment(match):
                if len(match) == 0:
                    match = 'null'
                else:
                    pass
                return match

            ## 正規表現を使用した住所解析
            scraping_list = address_result[9:] # 一文字ずつ分けて、かつ郵便番号を抜いたリスト(正規表現以外に使用)
            scraping_str = "".join(scraping_list) # 正規表現用の文字列

            # 「都道府県」の抽出
            Ken_match = re.match('東京都|北海道|京都府|大阪府|.+県', scraping_str).group()

            Ken_match_1list = n_gram(Ken_match, 1) # 県名を一文字ずつ分解(例)['奈', '良', '県']
            for i in Ken_match_1list:
                scraping_list.remove(i)
            scraping_str2 = "".join(scraping_list) # 県名を除去したstr

            # 「市区町村」の抽出
            City_match = re.match('.+[区町村]', scraping_str2).group()

            City_match_1list = n_gram(City_match, 1) # 市区町村の部分を除去
            for i in City_match_1list:
                scraping_list.remove(i)
            scraping_str3 = "".join(scraping_list)


            # 「町名」「番地」「ビル名」の抽出
            if '目' in scraping_str3:
                Town_match = re.match('.+丁目', scraping_str3).group() # 町名

                Town_match_1list = n_gram(Town_match, 1)
                for i in Town_match_1list:
                    scraping_list.remove(i)
                scraping_str4 = "".join(scraping_list)

                if '−' in scraping_str4:
                    num_match = re.match('\d+.\d+', scraping_str4).group() # 番地

                    num_match_1list = n_gram(num_match, 1)
                    for i in num_match_1list:
                        scraping_list.remove(i)
                    scraping_str5 = "".join(scraping_list)

                    build_match = scraping_str5 # ビル名

                else:
                    build_match = scraping_str4 # ビル名

                    num_match = 'null' # 番地

            elif '-' in scraping_str3:
                num_match = re.match('\d+.\d+', scraping_str3).group() # 番地

                Town_match = 'null' # 町名

                num_match_1list = n_gram(num_match, 1)
                for i in num_match_1list:
                    scraping_list.remove(i)
                scraping_str4 = "".join(scraping_list)

                build_match = scraping_str4 # ビル名

            else:
                build_match = scraping_str3 # ビル名

                Town_match = 'null' # 町名
                num_match = 'null' # 番地

            ## ここまでスクレイピング処理-----------------------------------------------------------------------------------

            ##APIを使用した、緯度経度変換処理
            def get_lat_lon_from_address(address_l):
                url = 'http://www.geocoding.jp/api/'
                latlons = []
                for address in tqdm(address_l):
                    payload = {"v": 1.1, 'q': address}
                    r = requests.get(url, params=payload)
                    ret = BS(r.content,'lxml')
                    if ret.find('error'):
                        raise ValueError(f"Invalid address submitted. {address}")
                    else:
                        lat = ret.find('lat').string
                        lon = ret.find('lng').string
                        latlons.append([lat,lon])
                        time.sleep(5)
                return latlons

            lat_lng_list = [] # 住所をリストにする
            lat_lng_list.append(scraping_str)
            lat_lng = get_lat_lon_from_address(lat_lng_list) # 関数の起動

            # 出力
            print('-------------------------')
            print(Judgment(postal_code))
            print(Judgment(Ken_match))
            print(Judgment(City_match))
            print(Judgment(Town_match))
            print(Judgment(num_match))
            print(Judgment(build_match))
            print(lat_lng)
            print('-------------------------')

            '''
            ## csv追記書き込み処理

            # スクレイピング情報を一つのリストにまとめる
            all_list.append(Judgment(postal_code))
            all_list.append(Judgment(Ken_match))
            all_list.append(Judgment(City_match))
            all_list.append(Judgment(Town_match))
            all_list.append(Judgment(num_match))
            all_list.append(Judgment(build_match))

            # 緯度経度の情報を合体させる
            all_list.extend(lat_lng)

            # 追記型の書き込み
            # pathの中に、csvファイルのパスを入力してください
            path = ''

            with open(path, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(all_list)

            all_list.clear() # スクレイピング情報を収納したリストを毎回空にする
            '''

            back_button = driver.find_element_by_xpath('//*[@id="pane"]/div/div[1]/div/div/button/span')
            back_button.click() # 検索一覧に戻ります
            count += 2
            roop_counter += 1
            time.sleep(5)

        # 次のページへ移動します
        next_button = driver.find_element_by_xpath('//*[@id="n7lv7yjyC35__section-pagination-button-next"]')
        next_button.click()
        time.sleep(5)

    except:
        driver.close() # 最後にブラウザを閉じる

































































