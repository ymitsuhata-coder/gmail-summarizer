import os
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
import google.auth
from flask import Flask

app = Flask(__name__)

# ★光畑社長のメールアドレス
OWNER_EMAIL = "y.mitsuhata@mseedpartner.com" 
# ★サービスアカウントのメールアドレス (image_2d0ce6.pngに載っていたもの)
SERVICE_ACCOUNT_EMAIL = "512310392497-compute@developer.gserviceaccount.com"

LINE_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

@app.route('/')
def gmail_to_line():
    try:
        # 1. 認証情報を取得
        scopes = ['https://www.googleapis.com/auth/gmail.readonly']
        credentials, project = google.auth.default(scopes=scopes)
        
        # 2. 社長になりすますための「委任」設定を正しく作り直す
        from google.auth import impersonated_credentials
        delegated_credentials = impersonated_credentials.Credentials(
            source_credentials=credentials,
            target_principal=SERVICE_ACCOUNT_EMAIL, # ここを明示しました
            target_scopes=scopes,
            # ここで「社長の代わりに」と指定します
            delegate_account=OWNER_EMAIL 
        )

        # もし上記でダメな場合、より直接的な「委任」方法を試します
        if hasattr(credentials, 'with_subject'):
            delegated_credentials = credentials.with_subject(OWNER_EMAIL)

        # 3. Gmailサービスを起動
        service = build('gmail', 'v1', credentials=delegated_credentials)

        # 4. 未読メール取得
        results = service.users().messages().list(userId=OWNER_EMAIL, q='is:unread', maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            return f"Gmailに未読メールはありません。システムは正常です。({OWNER_EMAIL})"

        # 5. 内容取得
        msg = service.users().messages().get(userId=OWNER_EMAIL, id=messages[0]['id']).execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '無題')
        
        # 6. LINE送信
        if LINE_TOKEN:
            url = "https://api.line.me/v2/bot/message/broadcast"
            headers_line = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_TOKEN}"
            }
            payload = {"messages": [{"type": "text", "text": f"新着メール通知:\n{subject}"}]}
            requests.post(url, headers=headers_line, json=payload)
            return f"成功！LINEに「{subject}」を通知しました！"
        else:
            return "LINEトークンが見つかりません。"

    except Exception as e:
        import traceback
        return f"【最終解析】エラーが発生しました: {str(e)}<br><pre>{traceback.format_exc()}</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
