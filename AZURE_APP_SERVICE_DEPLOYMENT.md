# Azure App Service デプロイメント完全ガイド

FastAPI バックエンドを Azure App Service (Linux / Python 3.12) にデプロイするための完全な手順書

## 📋 前提条件

- Azure サブスクリプション
- Azure CLI インストール済み
- GitHub アカウント
- ローカルで動作確認済みの FastAPI アプリケーション

## 🚀 デプロイ手順

### 1. Azure App Service の作成

#### 1.1 Azure CLI でログイン
```bash
az login
```

#### 1.2 リソースグループの作成（既存がある場合はスキップ）
```bash
# リソースグループ名とリージョンを指定
az group create --name rg-fastapi-app --location japaneast
```

#### 1.3 App Service Plan の作成
```bash
# Linux プラン、Python 3.12 対応
az appservice plan create \
  --name plan-fastapi-app \
  --resource-group rg-fastapi-app \
  --sku B1 \
  --is-linux
```

#### 1.4 App Service の作成
```bash
# App Service 名は全世界で一意である必要があります
az webapp create \
  --resource-group rg-fastapi-app \
  --plan plan-fastapi-app \
  --name your-fastapi-app-name \
  --runtime "PYTHON|3.12" \
  --deployment-local-git
```

### 2. Azure ポータルでの設定

#### 2.1 基本設定
Azure ポータル → App Services → your-fastapi-app-name → Configuration

**スタートアップ コマンド:**
```bash
bash startup.sh
```

**スタック設定:**
- スタック: Python
- メジャー バージョン: Python 3
- マイナー バージョン: Python 3.12

#### 2.2 環境変数の設定
Configuration → Application settings で以下を追加:

| 名前 | 値 | 説明 |
|------|-----|------|
| `MYSQL_HOST` | `rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com` | MySQL ホスト |
| `MYSQL_PORT` | `3306` | MySQL ポート |
| `MYSQL_USER` | `tech0gen10student` | MySQL ユーザー名 |
| `MYSQL_PASSWORD` | `your_password` | MySQL パスワード |
| `MYSQL_DATABASE` | `test_tanaka` | データベース名 |
| `MYSQL_SSL_CA` | `app/certs/DigiCertGlobalRootG2.crt` | SSL証明書パス |
| `SECRET_KEY` | `your_jwt_secret_key_here` | JWT シークレットキー |
| `ALGORITHM` | `HS256` | JWT アルゴリズム |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | トークン有効期限 |
| `ALLOWED_ORIGINS` | `["https://your-frontend-domain.com","http://localhost:3000"]` | CORS許可オリジン |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | ビルド自動実行 |
| `PYTHONPATH` | `/home/site/wwwroot` | Python パス |

### 3. MySQL ネットワーク設定

#### 3.1 App Service の送信 IP アドレス確認
```bash
az webapp show \
  --resource-group rg-fastapi-app \
  --name your-fastapi-app-name \
  --query possibleOutboundIpAddresses \
  --output tsv
```

#### 3.2 Azure MySQL ファイアウォール設定
Azure ポータル → Azure Database for MySQL servers → your-mysql-server → Networking

**ファイアウォール ルール:**
```
ルール名: AllowAppService
開始 IP: [App Service送信IPアドレス]
終了 IP: [App Service送信IPアドレス]
```

**注意:** 複数の送信IPアドレスがある場合は、すべてを追加してください。

### 4. GitHub Actions の設定

#### 4.1 Publish Profile のダウンロード
Azure ポータル → App Services → your-fastapi-app-name → 「発行プロファイルの取得」をクリック

#### 4.2 GitHub Secrets の設定
GitHub リポジトリ → Settings → Secrets and variables → Actions

**Secrets を追加:**
| 名前 | 値 |
|------|-----|
| `AZURE_APP_SERVICE_NAME` | `your-fastapi-app-name` |
| `AZURE_APP_SERVICE_PUBLISH_PROFILE` | 発行プロファイルの内容全体 |

### 5. デプロイの実行

#### 5.1 手動デプロイ（初回）
```bash
# リポジトリをプッシュ
git add .
git commit -m "Add Azure deployment configuration"
git push origin main
```

#### 5.2 GitHub Actions による自動デプロイ
- main ブランチへの push で自動的にデプロイが開始されます
- GitHub → Actions タブでデプロイ状況を確認できます

### 6. デプロイ後の確認

#### 6.1 アプリケーションの動作確認
```bash
# ヘルスチェック
curl https://your-fastapi-app-name.azurewebsites.net/health

# API ドキュメント
curl https://your-fastapi-app-name.azurewebsites.net/docs
```

#### 6.2 ログの確認
```bash
# Azure CLI でログストリーミング
az webapp log tail \
  --resource-group rg-fastapi-app \
  --name your-fastapi-app-name
```

#### 6.3 データベース接続確認
```bash
# SSH でコンテナに接続（Azure ポータルから）
python -c "
from app.db.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT VERSION()'))
    print('Database connected:', result.fetchone())
"
```

## 🔧 トラブルシューティング

### よくあるエラーと対策

#### エラー 1: "Application startup failed"
**原因:** startup.sh の実行権限不足
**対策:**
```bash
# ローカルで実行権限を付与してコミット
chmod +x startup.sh
git add startup.sh
git commit -m "Make startup.sh executable"
git push
```

#### エラー 2: "Database connection failed"
**原因:** MySQL ファイアウォール設定
**対策:**
1. App Service の送信 IP を確認
2. MySQL ファイアウォールに IP を追加
3. SSL 設定を確認

#### エラー 3: "Module not found"
**原因:** requirements.txt の依存関係不足
**対策:**
```bash
# requirements.txt を更新
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements.txt"
git push
```

#### エラー 4: "CORS policy error"
**原因:** CORS 設定が正しくない
**対策:**
App Service の環境変数 `ALLOWED_ORIGINS` を確認・更新

### デバッグコマンド

#### App Service コンテナ内での診断
```bash
# Azure ポータル → Development Tools → SSH で接続

# Python 環境確認
python --version
pip list

# 環境変数確認
printenv | grep MYSQL

# アプリケーション構造確認
ls -la /home/site/wwwroot/

# ログファイル確認
tail -f /var/log/supervisord.log
```

## 📊 パフォーマンス設定

### 推奨設定

#### Gunicorn ワーカー数の調整
startup.sh の `--workers` パラメータ:
- B1 プラン: 2-4 ワーカー
- S1 プラン: 4-6 ワーカー
- P1v2 プラン: 6-8 ワーカー

#### App Service プランのスケーリング
```bash
# プランをスケールアップ
az appservice plan update \
  --name plan-fastapi-app \
  --resource-group rg-fastapi-app \
  --sku S1
```

## 🔒 セキュリティ設定

### SSL/TLS 設定
Azure ポータル → App Services → TLS/SSL settings
- HTTPS Only: 有効
- Minimum TLS Version: 1.2

### カスタムドメイン（オプション）
```bash
# カスタムドメインの追加
az webapp config hostname add \
  --webapp-name your-fastapi-app-name \
  --resource-group rg-fastapi-app \
  --hostname your-custom-domain.com
```

## 📈 監視とロギング

### Application Insights の設定
```bash
# Application Insights の作成
az monitor app-insights component create \
  --app your-fastapi-app-insights \
  --location japaneast \
  --resource-group rg-fastapi-app

# App Service に接続
az webapp config appsettings set \
  --resource-group rg-fastapi-app \
  --name your-fastapi-app-name \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=your-instrumentation-key
```

## ✅ 成功確認チェックリスト

- [ ] App Service が正常に作成されている
- [ ] 環境変数がすべて設定されている
- [ ] MySQL ファイアウォールが設定されている
- [ ] GitHub Actions が正常に実行されている
- [ ] ヘルスチェック エンドポイントが応答する
- [ ] Swagger UI にアクセスできる
- [ ] データベース接続が確立されている
- [ ] Alembic マイグレーションが実行されている

## 🌐 アクセス URL

デプロイ完了後のアクセス先:
- **アプリケーション:** `https://your-fastapi-app-name.azurewebsites.net`
- **API ドキュメント:** `https://your-fastapi-app-name.azurewebsites.net/docs`
- **ヘルスチェック:** `https://your-fastapi-app-name.azurewebsites.net/health`

## 📞 サポート

問題が発生した場合:
1. Azure ポータルのログを確認
2. GitHub Actions のログを確認
3. この文書のトラブルシューティングセクションを参照
4. Azure サポートに問い合わせ