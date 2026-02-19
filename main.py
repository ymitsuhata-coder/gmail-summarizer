import os
import base64
import requests
from googleapiclient.discovery import build
import google.auth
from flask import Flask

app = Flask(__name__)

# トークンは環境変数から読み込む設定にしました（image_2c2520.pngの設定を活かします）
LINE_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

@app.route('/')
def gmail_to_line():
    try:
        # 1. 認証
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        # 2. Gmailサービスを起動（書き方を変更しました）
        service = build('gmail', 'v1', credentials=credentials)

        # 3. 未読メール取得
        results = service.users().messages().list(userId='me', q='is:unread', maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            return "未読メールはありません。待機中です。"

        # 4. 内容取得
        msg = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
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
