# BtoBtoC エネルギーマネージャー テスト手順

## 概要
従業員の個人生活におけるCO₂削減量を可視化し、ポイント付与・景品交換・社内ランキング・CSRレポート機能を提供するBtoBtoCアプリケーション。

## 重要検証コマンド

### 1. ヘルスチェック（503エラー修復確認）
```bash
# 本番環境のヘルスチェック（200固定化を目標）
curl -i https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/health

# 期待結果: HTTP/1.1 200 OK
# レスポンス例:
# {
#   "status": "healthy",
#   "app": "エネルギーマネージャー API",
#   "version": "1.0.0",
#   "database": "接続正常",
#   "timestamp": "2025-01-18T12:00:00Z"
# }
```

### 2. CORS付きトークン取得（ログイン機能確認）
```bash
# ログイン（URLSearchParams形式）
curl -i -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Origin: https://app-002-gen10-step3-2-node-oshima2.azurewebsites.net" \
  --data-urlencode "username=admin@example.com" \
  --data-urlencode "password=StrongP@ssw0rd!" \
  https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/login/access-token

# 期待結果: HTTP/1.1 200 OK
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "token_type": "bearer"
# }
```

### 3. 認証ユーザー情報取得
```bash
# Bearer認証でユーザー情報取得
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
curl -i -H "Authorization: Bearer $TOKEN" \
  https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/users/me

# 期待結果: ユーザー情報（日本語表示）
```

### 4. 新機能APIテスト

#### ポイント関連API
```bash
# 自分のポイント情報取得
curl -i -H "Authorization: Bearer $TOKEN" \
  https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/points/me

# ポイント履歴取得
curl -i -H "Authorization: Bearer $TOKEN" \
  "https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/points/history?limit=10"

# ランキング取得
curl -i -H "Authorization: Bearer $TOKEN" \
  "https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/points/ranking?period=monthly"
```

#### 景品関連API
```bash
# 景品一覧取得
curl -i -H "Authorization: Bearer $TOKEN" \
  "https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/rewards?page=1&limit=10"

# 景品交換
curl -i -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reward_id": 1}' \
  https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/rewards/exchange

# 交換履歴取得
curl -i -H "Authorization: Bearer $TOKEN" \
  https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/rewards/my-redemptions
```

#### 管理者API（要スーパーユーザー権限）
```bash
# ポイントルール一覧
curl -i -H "Authorization: Bearer $TOKEN" \
  https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/admin/points-rules

# CSRレポートエクスポート
curl -i -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "range_start": "2025-01-01",
    "range_end": "2025-01-31",
    "granularity": "monthly",
    "format": "csv"
  }' \
  https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1/reports/csr-export
```

## データベース初期化手順

### 1. Alembicマイグレーション実行
```bash
# バックエンドディレクトリに移動
cd /Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend

# 仮想環境のPythonでマイグレーション実行（App Service内）
/home/site/wwwroot/antenv/bin/python -m alembic upgrade head
```

### 2. 初期データ投入（開発用）
```python
# 削減記録のサンプルデータ
INSERT INTO reduction_records (user_id, date, energy_type, usage, baseline, reduced_co2_kg) VALUES
(1, '2025-01-01', 'electricity', 300, 350, 2.5),
(1, '2025-01-02', 'gas', 50, 60, 1.8),
(2, '2025-01-01', 'electricity', 280, 340, 3.0),
(2, '2025-01-02', 'gas', 45, 55, 1.5);

# ポイントルールのサンプル
INSERT INTO point_rules (name, rule_type, value, active) VALUES
('基本CO₂削減ポイント', 'per_kg', 10.0, true),
('月間ランキングボーナス', 'rank_bonus', 50.0, true);

# 景品のサンプル
INSERT INTO rewards (title, description, category, stock, points_required, active) VALUES
('Amazonギフトカード 500円分', 'Amazon.co.jpで使えるギフトカード', 'ギフトカード', 20, 500, true),
('スターバックス ドリンクチケット', 'Tallサイズまでのドリンク1杯', '商品', 15, 400, true),
('社内カフェ利用券', '社内カフェで使える500円分の利用券', '社内サービス', 50, 300, true);
```

## E2Eテストシナリオ

### シナリオ1: ログイン〜ダッシュボード表示
1. フロントエンド：https://app-002-gen10-step3-2-node-oshima2.azurewebsites.net/login
2. 管理者アカウントでログイン（admin@example.com / StrongP@ssw0rd!）
3. `/dashboard` にリダイレクト
4. 日本語でダッシュボード表示（CO₂削減量、ポイント、順位）

### シナリオ2: ランキング確認
1. ナビゲーションから「社員ランキング」をクリック
2. 期間フィルタ（今月/四半期/年間）を変更
3. 部門フィルタで絞り込み
4. ランキングが正しく表示される

### シナリオ3: 景品交換
1. 「景品交換」ページに移動
2. 景品を検索・フィルタ
3. ポイント十分な景品で「交換する」をクリック
4. 確認ダイアログで「はい」
5. 交換履歴に反映される

### シナリオ4: 管理者機能
1. 管理者権限で `/admin` にアクセス
2. CSRレポート出力パラメータを設定
3. 「CSVでエクスポート」をクリック
4. 日本語のCSVファイルがダウンロードされる

## フロントエンド開発サーバー起動

```bash
cd /Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_frontend

# 依存関係インストール
npm install

# 環境変数設定（.env.local作成）
echo "NEXT_PUBLIC_API_BASE=https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net/api/v1" > .env.local

# 開発サーバー起動
npm run dev

# ブラウザで http://localhost:3000 にアクセス
```

## バックエンド開発サーバー起動

```bash
cd /Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend

# 仮想環境作成・有効化
python -m venv venv
source venv/bin/activate  # macOS/Linux
# または venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定（.env作成）
cat > .env << EOF
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=energy_manager
FIRST_SUPERUSER_EMAIL=admin@example.com
FIRST_SUPERUSER_PASSWORD=StrongP@ssw0rd!
ALLOWED_ORIGINS=["http://localhost:3000", "https://app-002-gen10-step3-2-node-oshima2.azurewebsites.net"]
EOF

# マイグレーション実行
alembic upgrade head

# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## トラブルシューティング

### 503エラーが再発する場合
1. App Service設定を確認：
   - **Startup Command**: `bash startup.sh`
   - **SCM_DO_BUILD_DURING_DEPLOYMENT**: `false`
   - **WEBSITE_RUN_FROM_PACKAGE**: `0`

2. Antenvの確認：
```bash
# SSH接続してantenvが存在するか確認
ls -la /home/site/wwwroot/antenv/bin/python
```

### ログイン失敗の場合
1. CORS設定を確認
2. ブラウザの開発者ツールでネットワークタブを確認
3. バックエンドログを確認：Azure Portal > App Service > Log stream

### データベース接続エラー
1. MySQL SSL証明書パス確認：`app/certs/DigiCertGlobalRootG2.crt`
2. 接続文字列の確認
3. ファイアウォール設定確認

## 日本語化確認項目

- [x] ログインページ（メールアドレス、パスワード、エラーメッセージ）
- [x] ダッシュボード（統計、グラフタイトル、メニュー）
- [x] ランキング（期間、部門、順位表示）
- [x] ポイント（履歴、残高、獲得・消費）
- [x] 景品交換（カテゴリ、検索、交換確認）
- [x] 管理画面（CSRレポート、統計）
- [x] APIレスポンス（エラーメッセージ）
- [x] CSVレポート（見出し、注釈）

## 成果物の確認

### バックエンド
- [x] startup.sh修正（prebuilt venv対応）
- [x] main.py修正（503エラー対策、日本語メッセージ）
- [x] 新DBスキーマ（Alembicマイグレーション）
- [x] 新API実装（points, rewards, admin, reports）
- [x] 全APIレスポンス日本語化

### フロントエンド
- [x] i18n/ja.ts（日本語文言一元管理）
- [x] ダッシュボード改修（BtoBtoC対応）
- [x] 新ページ実装（ranking, points, rewards, admin）
- [x] 全UI日本語化
- [x] エラーハンドリング日本語化

### インフラ
- [x] GitHub Actions（prebuilt venv方式）
- [x] web.config（Linux App Service対応）
- [x] startup.sh（安定起動）

これで、ログイン再発事故の防止とBtoBtoC機能の完全日本語化が完了しました。