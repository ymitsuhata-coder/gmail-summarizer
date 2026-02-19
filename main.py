import os
import requests
from googleapiclient.discovery import build
import google.auth
from flask import Flask

app = Flask(__name__)

# ★ここを光畑社長のメールアドレスに書き換えてください★
OWNER_EMAIL = "y.mitsuhata@mseedpartner.com" 

LINE_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

@app.route('/')
def gmail_to_line():
    try:
        # 1. 認証設定
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        # 2. 社長として行動する（Delegationの設定）
        delegated_credentials = credentials.with_subject(OWNER_EMAIL)
        service = build('gmail', 'v1', credentials=delegated_credentials)

        # 3. 未読メール取得 (userId を 'me' から OWNER_EMAIL に変更)
        results = service.users().messages().list(userId=OWNER_EMAIL, q='is:unread', maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            return f"未読メールはありません。({OWNER_EMAIL})"

        # 4. 内容取得
        msg = service.users().messages().get(userId=OWNER_EMAIL, id=messages[0]['id']).execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '無題')
        
        # 5. LINE送信
        if LINE_TOKEN:
            url = "https://api.line.me/v2/bot/message/broadcast"
            headers_line = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_TOKEN}"
            }
            payload = {"messages": [{"type": "text", "text": f"新着メール通知:\n{subject}"}]}
            requests.post(url, headers=headers_line, json=payload)
            return f"LINEに「{subject}」を通知しました！"
        else:
            return "LINEトークンが設定されていません。"

    except Exception as e:
        import traceback
        return f"【解析用詳細】エラーが発生しました: {str(e)}<br><pre>{traceback.format_exc()}</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
