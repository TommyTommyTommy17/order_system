# Pythonのバージョンを指定
FROM python:3.12

# フォルダの作成
WORKDIR /code

# 必要なソフトをインストール
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# プログラムをコピー
COPY . /code/