# MiniMaid
Discordで便利な機能を提供するオープンソースのBotです。

# 理念

- オープンソースである
- 初心者でも簡単にホストができる
- モデレーション機能がない

これらの理念をもとにBotを制作しています。Pull Requestは大歓迎です。

また、こういう機能が欲しい、という要望があればissueを受け付けています。

公式での運用をしています→[導入リンク](https://discord.com/api/oauth2/authorize?client_id=522305114757791754&permissions=4231392849&scope=bot)

（可用性の保証は致しません。利用者にて独自にホストし運用することを推奨しています。）


# 機能
チェックマークがあるものは完了しています。

[コマンド一覧はこちら](https://github.com/sizumita/MiniMaid/blob/master/docs/Commands.md)

- [ ] ヘルプコマンド
- [x] チーム分け
- [ ] ダイス
    - [ ] nCr
- [x] mp3、wavファイルの再生
- [x] ボイスチャットの録音
- [x] VoiceChatでの読み上げ
    - [x] OpenJTalk speech
    - [x] 入退室コマンド
    - [x] 読み上げのスキップ
    - [x] 各種設定の変更
- [x] RSS Readerの機能
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
- install mpg123
    - `apt install mpg123`
    - `brew install mpg123`
    - you can install if your package manager
    - otherwise you can install from https://www.mpg123.de/download.shtml
- run `python -m venv venv`
- run `source ./venv/bin/activate`
- run `pip install -r requirements.txt`
- run `source .env`
- run `alembic upgrade head`
- run `python main.py`

# Herokuでのデプロイ

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

上のボタンを押し，BOTのトークン等の情報を入れることでもBOTをデプロイすることができます．

料金体系については[こちら](https://www.heroku.com/pricing)をご覧ください.
基本的に無料ですがいくつかの制約事項があります．
