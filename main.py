import os
import requests
from googleapiclient.discovery import build
import google.auth
from flask import Flask

app = Flask(__name__)

# ★社長のアドレス
OWNER_EMAIL = "y.mitsuhata@mseedpartner.com" 
LINE_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

@app.route('/')
def gmail_to_line():
    try:
        # 最も標準的な認証
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        # 社長のアカウントとして動作するよう直接指定
        if hasattr(credentials, 'with_subject'):
            credentials = credentials.with_subject(OWNER_EMAIL)

        service = build('gmail', 'v1', credentials=credentials)

        # 未読チェック
        results = service.users().messages().list(userId=OWNER_EMAIL, q='is:unread', maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            return f"正常稼働中：未読メールはありません。({OWNER_EMAIL})"

        # LINE送信
        if LINE_TOKEN:
            url = "https://api.line.me/v2/bot/message/broadcast"
            headers_line = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
            payload = {"messages": [{"type": "text", "text": "新着メールがあります！"}]}
            requests.post(url, headers=headers_line, json=payload)
            return "成功！LINEを鳴らしました。"
        return "LINEトークン未設定"

    except Exception as e:
        return f"エラー詳細: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
