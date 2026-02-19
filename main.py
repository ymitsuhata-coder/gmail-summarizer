import os
import base64
from google.cloud import gmail_v1
import google.auth
from flask import Flask
import requests
import json

app = Flask(__name__)

# --- 光畑社長専用設定（トークン組み込み済み） ---
LINE_NOTIFY_TOKEN = "lnRShFGScSTJj/2gX1UnBRnhZlm9cQkjxb5aD8KXnVMlUC8FL7hLgq7D0vt5GTa1swFxobXvEVa/Bsyles8Y7/BHxOa9Bl7JqP6wxF96+24yZSVEBDLw176lDUFwWlo2q/7Qf6Ngfs30GcfUByGpwdB04t89/1O/w1cDnyilFU="

def summarize_text(text):
    # まずは疎通確認用：最初の100文字を抽出
    return text[:100].replace('\n', ' ') + "..."

@app.route('/')
def gmail_to_line():
    try:
        # 1. Gmail APIの認証
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        service = gmail_v1.Gmail(credentials=credentials)

        # 2. 未読メールの取得（最新1件）
        results = service.users().messages().list(userId='me', q='is:unread', maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            return "新着の未読メールはありませんでした。正常に動作しています。"

        # 3. メール内容の解析
        msg = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
        payload = msg['payload']
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '無題')
        
        # 本文の抽出
        body_data = ""
        if 'data' in payload['body']:
            body_data = payload['body']['data']
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    body_data = part['body']['data']
                    break
        
        if body_data:
            body_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
            summary = summarize_text(body_text)
        else:
            summary = "本文の取得に失敗しました（HTML形式の可能性があります）"

        # 4. LINE Notifyへの送信
        line_url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"}
        message = f"\n【件名】: {subject}\n【要約】: {summary}"
        
        response = requests.post(line_url, headers=headers, data={"message": message})
        
        if response.status_code == 200:
            return "LINEに要約を送信しました！スマホを確認してください。"
        else:
            return f"LINE送信エラー: {response.text}"

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
