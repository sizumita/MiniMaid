# MiniMaid
チーム分けや投票など、モデレーション以外の機能を搭載した多機能Botです。
公式での運用をしています→[導入リンク](https://discord.com/api/oauth2/authorize?client_id=522305114757791754&permissions=4231392849&scope=bot)
（可用性の保障はいたしません。Bot運用を推奨しています。）


# 機能
チェックマークがあるものは完了しています。

- [ ] ヘルプコマンド
- [x] チーム分け
- [ ] ダイス
    - [ ] nCr
- [x] VoiceChatでの読み上げ
    - [x] OpenJTalk speech
    - [x] 入退室コマンド
    - [x] 読み上げのスキップ
    - [x] 各種設定の変更
- [x] 投票システム
- [x] パーティー
    - [x] パーティの作成
    - [x] パーティーへの参加
    - [x] パーティーからの脱退
    - [x] パーティーメンバー呼び出し (パーティーメンバー全員にメンションをする)
- [ ] タイマー
    - [ ] タイマーセット


## 実装優先度が低い機能
- [ ] youtube music player
    - [ ] queue
    - [ ] skip
    - [ ] jump any place (e.g. 23sec)
    - [ ] delete queue
    - [ ] shuffle queue
    - [ ] clear queue
- [ ] music playlist
    - [ ] create playlist
    - [ ] modify playlist
    - [ ] play playlist
    - [ ] delete playlist
    - [ ] shuffle playlist
- [ ] 日程調整機能


# 開発者向け

## Installation

### using docker / docker-compose

- pull this repo
- install docker and docker-compose
- build and run

### using Python

- pull https://github.com/sizumita/jtalkdll.git
- run 
  ```bash
  cd jtalkdll
  bash build
  ```
- run `rm rf -d jtalkdll` if you want
- pull this repo
- install Python 3.8 or later
- run `python -m venv venv`
- run `source ./venv/bin/activate`
- run `pip install -r requirements.txt`
- run `source .env && python main.py`

# Heroku support

Click the button below to deploy to Heroku.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

For more information about pricing, please refer to [here](https://www.heroku.com/pricing).
