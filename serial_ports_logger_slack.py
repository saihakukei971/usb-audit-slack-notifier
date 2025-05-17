import sys
import os
import csv
import socket
import datetime
import argparse
import serial.tools.list_ports
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import tomli
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("serial_logger.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def temp_path(relative_path):
    """リソースへのパスを取得する（PyInstaller対応）"""
    try:
        # PyInstallerでパッケージングされている場合の一時パス取得
        base_path = sys._MEIPASS
    except Exception:
        # 通常実行時は現在のディレクトリを使用
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_serial_ports_info():
    """すべてのシリアルポート情報を取得する"""
    ports = list(serial.tools.list_ports.comports())
    ports_info = []

    for p in ports:
        # VID/PIDが取得できる場合は16進数に変換
        vid = None
        if p.vid is not None:
            vid = str.upper(((hex(p.vid)).replace("0x",""))).zfill(4)

        pid = None
        if p.pid is not None:
            pid = str.upper(((hex(p.pid)).replace("0x",""))).zfill(4)

        # ポート情報をディクショナリとして格納
        port_info = {
            'hostname': socket.gethostname(),
            'port': p.device,
            'description': p.description,
            'vid': vid,
            'pid': pid,
            'serial_number': p.serial_number if p.serial_number else "",
            'manufacturer': p.manufacturer if p.manufacturer else ""
        }
        ports_info.append(port_info)

    return ports_info

def save_to_csv(ports_info):
    """シリアルポート情報をCSVファイルに保存する"""
    # CSVフォルダがなければ作成
    csv_dir = "csv_logs"
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    # 現在の日時を取得してファイル名に使用
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    hostname = socket.gethostname()

    # ファイル名の形式: serial_ports_<hostname>_YYYYMMDD_HHMMSS.csv
    filename = f"serial_ports_{hostname}_{timestamp}.csv"
    file_path = os.path.join(csv_dir, filename)

    # DataFrameを作成してCSVに保存
    df = pd.DataFrame(ports_info)
    df.to_csv(file_path, index=False)

    logger.info(f"CSVファイルを保存しました: {file_path}")
    return file_path

def load_slack_settings():
    """Slack設定をTOMLファイルから読み込む"""
    try:
        with open("slack_settings.toml", "rb") as f:
            config = tomli.load(f)
        return config.get("slack", {})
    except Exception as e:
        logger.error(f"Slack設定の読み込みに失敗しました: {e}")
        return {}

def upload_to_slack(file_path, slack_settings):
    """CSVファイルをSlackにアップロードする"""
    token = slack_settings.get("token")
    channel = slack_settings.get("channel")

    if not token or not channel:
        logger.error("Slackトークンまたはチャンネルが設定されていません")
        return False

    try:
        # Slackクライアントを初期化
        client = WebClient(token=token)

        # 現在の日付を取得して通知文を作成
        today = datetime.datetime.now().strftime("%Y年%m月%d日")
        message = f"{today}のシリアルポートの一覧取得をしました。ご確認をお願いいたします。"

        # ファイルアップロード
        response = client.files_upload_v2(
            channels=channel,
            file=file_path,
            title=os.path.basename(file_path),
            initial_comment=message
        )

        logger.info(f"SlackにCSVファイルをアップロードしました: {file_path}")
        logger.info(f"通知メッセージ: {message}")
        return True

    except SlackApiError as e:
        logger.error(f"Slackへのアップロードに失敗しました: {e}")
        return False

def main():
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description="Serial Ports Logger with Slack Integration")
    parser.add_argument("--silent", action="store_true", help="サイレントモードで実行（GUIなし）")
    args = parser.parse_args()

    try:
        # シリアルポート情報の取得
        ports_info = get_serial_ports_info()

        if not ports_info:
            logger.info("接続されているシリアルポートが見つかりませんでした")
            # 空のデータセットでもCSV作成
            ports_info = [{
                'hostname': socket.gethostname(),
                'port': "",
                'description': "No devices found",
                'vid': "",
                'pid': "",
                'serial_number': "",
                'manufacturer': ""
            }]

        # CSVに保存
        file_path = save_to_csv(ports_info)

        # Slack設定を読み込む
        slack_settings = load_slack_settings()

        # Slackにアップロード
        upload_result = upload_to_slack(file_path, slack_settings)

        if not upload_result:
            logger.warning("Slackへのアップロードに失敗しましたが、CSVは保存されています")

    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())