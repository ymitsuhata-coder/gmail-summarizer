import os
import base64
import requests
from google.cloud import gmail_v1
import google.auth
from flask import Flask

app = Flask(__name__)

# トークンを直接流し込みました
LINE_TOKEN = "/lnRShFGScSTJj/2gX1UnBRnhZlm9cQkjxb5aD8KXnVMlUC8FL7hLgq7D0vt5GTa1swFxobXvEVa/Bsyles8Y7/BHxOa9Bl7JqP6wxF96+24yZSVEBDLw176lDUFwWlo2q/7Qf6Ngfs30GcfUByGpwdB04t89/1O/w1cDnyilFU="

@app.route('/')
def gmail_to_line():
    try:
        # 1. 認証
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        service = gmail_v1.Gmail(credentials=credentials)

        # 2. 未読メール取得
        results = service.users().messages().list(userId='me', q='is:unread', maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            return "Gmailの未読メールはありませんでした。システムは正常に動いています。"

        # 3. 内容取得
        msg = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '無題')
        
        # 4. LINE送信 (Messaging API)
        url = "https://api.line.me/v2/bot/message/broadcast"
        headers_line = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        }
        payload = {"messages": [{"type": "text", "text": f"新着メール: {subject}"}]}
        requests.post(url, headers=headers_line, json=payload)

        return f"LINEに「{subject}」を通知しました！"

    except Exception as e:
        # エラーの内容をブラウザに直接表示させます
        return f"【解析中】エラーが発生しました: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
