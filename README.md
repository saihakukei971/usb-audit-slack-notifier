# USB-Audit-Slack-Notifier

## 概要
USB-Audit-Slack-Notifierは企業内の全Windows端末に接続されたUSBシリアルデバイス情報を自動収集し、CSVファイルとしてSlackチャンネルに通知するシステムです。このツールにより、情報システム部門は社内端末の周辺機器監査や資産管理を効率化できます。

## 使用技術
* Python 3.9+
* pyserial（シリアルポート情報取得）
* pandas（CSV処理）
* tomli（TOML設定ファイル解析）
* slack_sdk（Slack連携）
* Active Directory GPO（自動展開）
* Windows Task Scheduler（定期実行）
* PyInstaller（配布用exe生成）

## 処理の流れ
1. Windows起動時にGPOによりバッチファイルが自動実行される
2. スクリプトがシリアルポート情報を収集（VID/PID/製造元など）
3. ホスト名とタイムスタンプを付加してCSVファイルとして保存
4. Slack APIを使用して特定チャンネルにCSVファイルを添付し、**処理実行日を動的に反映した定型メッセージ**で通知
5. 管理者が通知を確認し、デバイス接続状況を把握

## 特徴・工夫した点
* **完全無人運用**: GPO配布とタスクスケジューラ連携でユーザー操作不要
* **効率的なエラーハンドリング**: ネットワーク切断時も情報損失なく後続処理を継続
* **16進数変換最適化**: VID/PID情報の変換処理を効率化し、パフォーマンス向上
* **セキュアな設定管理**: Slackトークンを分離配置し、リポジトリ内では非公開
* **スケーラビリティ**: 数千台規模の環境でも安定動作する処理方式

## セットアップ手順
1. リポジトリをクローン
   ```bash
   git clone https://github.com/yourusername/usb-audit-slack-notifier.git
   cd usb-audit-slack-notifier
   ```

2. 依存パッケージのインストール
   ```bash
   pip install pyserial pandas slack_sdk tomli
   ```

3. Slack設定ファイルの準備
   ```bash
   # slack_settings.tomlを作成して以下のように設定
   [slack]
   token = "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
   channel = "#usb-log"
   ```

4. テスト実行
   ```bash
   python serial_ports_logger_slack.py
   # CSVファイルの生成とSlack通知を確認
   ```

5. 実行ファイル生成と配布
   ```bash
   pip install pyinstaller
   pyinstaller --onefile --noconsole serial_ports_logger_slack.py
   # distフォルダ内の.exeファイルを共有フォルダに配置
   ```

## デモ
システム導入後は以下のようなワークフローが自動化されます：

1. 端末起動時に自動実行
2. CSV形式でデバイス情報を記録：
   ```
   hostname,port,description,vid,pid,serial_number,manufacturer
   PC001,COM3,USB Serial Port,0403,6001,FTYXY1234,FTDI
   ```
3. Slackチャンネルで通知を受信：
   * CSVファイルが添付される
   * **処理実行日の日付を動的に反映した定型メッセージが表示される**
     例：「2025年05月18日のシリアルポートの一覧取得をしました。ご確認をお願いいたします。」
   * この日付は実行時の現在日付が自動的に使用される

## なぜexeファイルをGitに含めないのか

PyInstallerで生成されるexeファイルをGitリポジトリに含めない理由は主に以下の技術的観点からです：

1. **バイナリサイズと差分管理の非効率性**：
   * .exeファイルは数十MBに達することがあり、Gitの差分管理に適さない
   * わずかなコード変更でもバイナリ全体が変更されるため、履歴管理が困難

2. **環境依存性**：
   * ビルド環境のPythonバージョンやライブラリに依存
   * 異なるWindows環境（7/10/11）向けに最適化が必要

3. **セキュリティリスク**：
   * バイナリファイルはビルド時の環境情報を含む可能性があり、セキュリティ上の懸念
   * ソースコードのみを管理し、デプロイ環境でビルドする方が安全

4. **CI/CD統合の柔軟性**：
   * ビルドプロセスをCI/CDパイプラインに組み込むことで品質管理が容易
   * 環境ごとに最適化されたビルドを自動生成できる

上級エンジニアであれば、リポジトリにはソースコードと明確なビルド手順のみを含め、バイナリは別途管理するのがベストプラクティスと理解しています。

## リポジトリ構成
```
usb-audit-slack-notifier/
├─ serial_ports_logger_slack.py  # メインスクリプト
├─ slack_settings.toml           # Slack設定ファイル（gitでは除外）
├─ run_logger.bat                # GPO配布用バッチファイル
├─ csv_logs/                     # CSV出力フォルダ（自動生成）
└─ README.md                     # 本文書
```

## requirements.txt
```
pyserial==3.5
pandas==2.0.3
slack_sdk==3.21.3
tomli==2.0.1
```
