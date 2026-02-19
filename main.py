import os
import base64
import requests
from google.cloud import gmail_v1
import google.auth
from flask import Flask

app = Flask(__name__)

# --- 光畑社長専用設定（Messaging API用） ---
# image_2ba8c3.png のトークンをここに組み込みました
LINE_CHANNEL_ACCESS_TOKEN = "/lnRShFGScSTJj/2gX1UnBRnhZlm9cQkjxb5aD8KXnVMlUC8FL7hLgq7D0vt5GTa1swFxobXvEVa/Bsyles8Y7/BHxOa9Bl7JqP6wxF96+24yZSVEBDLw176lDUFwWlo2q/7Qf6Ngfs30GcfUByGpwdB04t89/1O/w1cDnyilFU="

def send_line_message(text):
    """Messaging APIを使用してLINEを送る"""
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code

@app.route('/')
def gmail_to_line():
    try:
        # 1. Gmail API認証
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        service = gmail_v1.Gmail(credentials=credentials)

        # 2. 未読メール取得
        results = service.users().messages().list(userId='me', q='is:unread', maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            return "新着メールはありません。正常に待機中です。"

        # 3. 内容取得
        msg = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '無題')
        
        message_text = f"【新着メール】\n件名: {subject}\n\n※詳細はGmailを確認してください。"

        # 4. LINE送信
        status = send_line_message(message_text)
        
        if status == 200:
            return "LINEに通知を送信しました！"
        else:
            return f"LINE送信失敗(Status:{status})。トークンを確認してください。"

    except Exception as e:
        return f"エラー発生: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
