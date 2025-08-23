#!/usr/bin/env python3
"""
Azure MySQL ダミーデータ生成スクリプト
従業員15,000人規模の本番サイズデータを生成し、
管理画面とモバイル版の統合テスト用データを提供
"""

import os
import sys
import argparse
import logging
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# 依存関係
try:
    import mysql.connector
    from mysql.connector import Error
    from dotenv import load_dotenv
    from tqdm import tqdm
    import bcrypt
except ImportError as e:
    print(f"必要なライブラリがインストールされていません: {e}")
    print("pip install python-dotenv mysql-connector-python tqdm bcrypt を実行してください")
    sys.exit(1)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('seed_db.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TableSchema:
    """テーブルスキーマ情報"""
    name: str
    columns: Dict[str, Dict[str, Any]]
    primary_key: List[str]

class DatabaseSeeder:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.schemas = {}
        self.start_time = datetime.now()
        
        # データ生成パラメータ
        self.employees_count = config.get('employees', 15000)
        self.months_back = config.get('months', 24)
        self.active_rate = config.get('active_rate', 0.6)
        self.active_employees = int(self.employees_count * self.active_rate)
        
        # 季節性係数（月別）
        self.seasonal_factors = {
            1: 1.3,   # 1月 冬
            2: 1.25,  # 2月 冬
            3: 1.1,   # 3月 春
            4: 0.9,   # 4月 春
            5: 0.85,  # 5月 春
            6: 1.1,   # 6月 梅雨
            7: 1.35,  # 7月 夏
            8: 1.4,   # 8月 夏
            9: 1.2,   # 9月 残暑
            10: 0.9,  # 10月 秋
            11: 0.95, # 11月 秋
            12: 1.2   # 12月 冬
        }
        
        # 統計用カウンタ
        self.stats = {
            'companies': 0,
            'users': 0,
            'employees': 0,
            'energy_records': 0,
            'rewards': 0,
            'points_ledger': 0,
            'redemptions': 0
        }

    def connect(self):
        """Azure MySQL接続"""
        # 接続設定をログ出力（パスワードは隠す）
        config_log = {k: v for k, v in self.config.items()}
        config_log['password'] = '***' if config_log.get('password') else 'None'
        logger.info(f"接続設定: {config_log}")
        
        # SSL証明書ファイル存在確認
        ssl_ca_path = self.config.get('ssl_ca')
        if ssl_ca_path and not os.path.exists(ssl_ca_path):
            logger.error(f"SSL証明書ファイルが見つかりません: {ssl_ca_path}")
            return False
        
        try:
            # MySQL接続パラメータ
            connection_params = {
                'host': self.config['host'],
                'port': self.config['port'],
                'user': self.config['user'],
                'password': self.config['password'],
                'database': self.config['database'],
                'ssl_disabled': False,
                'ssl_verify_cert': True,
                'autocommit': False,
                'use_unicode': True,
                'charset': 'utf8mb4'
            }
            
            # SSL証明書が存在する場合のみ追加
            if ssl_ca_path and os.path.exists(ssl_ca_path):
                connection_params['ssl_ca'] = ssl_ca_path
                connection_params['ssl_verify_identity'] = True  # ホスト名検証追加
                logger.info(f"SSL証明書使用: {ssl_ca_path} (ホスト名検証有効)")
            else:
                logger.warning("SSL証明書なしで接続試行")
            
            self.connection = mysql.connector.connect(**connection_params)
            logger.info(f"Azure MySQL接続成功: {self.config['host']}")
            return True
            
        except Error as e:
            logger.error(f"データベース接続失敗: {e}")
            logger.error(f"エラーコード: {e.errno}, SQLState: {e.sqlstate if hasattr(e, 'sqlstate') else 'N/A'}")
            
            # 接続テスト用コマンドを提案
            logger.info("=== 手動接続テスト用コマンド ===")
            test_cmd = f"mysql -h {self.config['host']} -P {self.config['port']} -u {self.config['user']} -p{self.config['database']} --ssl-mode=REQUIRED"
            if ssl_ca_path and os.path.exists(ssl_ca_path):
                test_cmd += f" --ssl-ca={ssl_ca_path}"
            logger.info(f"コマンド: {test_cmd}")
            logger.info("※ パスワードは手動入力")
            
            return False

    def get_table_schema(self, table_name: str) -> Optional[TableSchema]:
        """テーブルスキーマ取得"""
        if not self.connection:
            return None
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # カラム情報取得
            cursor.execute(f"DESCRIBE {self.config['database']}.{table_name}")
            columns = {}
            primary_key = []
            
            for row in cursor.fetchall():
                col_name = row['Field']
                columns[col_name] = {
                    'type': row['Type'],
                    'null': row['Null'] == 'YES',
                    'key': row['Key'],
                    'default': row['Default'],
                    'extra': row['Extra']
                }
                if row['Key'] == 'PRI':
                    primary_key.append(col_name)
            
            cursor.close()
            return TableSchema(table_name, columns, primary_key)
            
        except Error as e:
            logger.warning(f"テーブル {table_name} のスキーマ取得失敗: {e}")
            return None

    def load_schemas(self):
        """必要なテーブルのスキーマを読み込み"""
        tables = [
            'companies', 'users', 'employees', 'energy_records',
            'rewards', 'points', 'points_ledger', 'redemptions', 'rankings'
        ]
        
        for table in tables:
            schema = self.get_table_schema(table)
            if schema:
                self.schemas[table] = schema
                logger.info(f"テーブル {table}: {len(schema.columns)}カラム")
            else:
                logger.warning(f"テーブル {table} が存在しないか、アクセスできません")

    def bulk_insert(self, table_name: str, data: List[Dict[str, Any]], batch_size: int = 1000):
        """バルクINSERT（冪等性対応）"""
        if not data:
            return 0
            
        schema = self.schemas.get(table_name)
        if not schema:
            logger.error(f"テーブル {table_name} のスキーマが見つかりません")
            return 0

        cursor = self.connection.cursor()
        total_inserted = 0
        
        try:
            # 有効なカラムのみフィルタリング
            valid_columns = set(schema.columns.keys())
            filtered_data = []
            
            for row in data:
                filtered_row = {k: v for k, v in row.items() if k in valid_columns}
                filtered_data.append(filtered_row)
            
            if not filtered_data:
                return 0
                
            columns = list(filtered_data[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            
            # ON DUPLICATE KEY UPDATE構築
            update_clause = ', '.join([f"{col}=VALUES({col})" for col in columns 
                                     if col not in schema.primary_key])
            
            sql = f"""
                INSERT INTO {self.config['database']}.{table_name} 
                ({', '.join(columns)}) 
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {update_clause}
            """
            
            # バッチ処理
            for i in tqdm(range(0, len(filtered_data), batch_size), 
                         desc=f"Inserting {table_name}"):
                batch = filtered_data[i:i + batch_size]
                values = [tuple(row[col] for col in columns) for row in batch]
                
                cursor.executemany(sql, values)
                total_inserted += cursor.rowcount
                
                # 定期的にコミット
                if i % (batch_size * 5) == 0:
                    self.connection.commit()
            
            self.connection.commit()
            logger.info(f"{table_name}: {total_inserted}件 処理完了")
            
        except Error as e:
            logger.error(f"{table_name} バルクINSERT失敗: {e}")
            self.connection.rollback()
            return 0
        finally:
            cursor.close()
            
        return total_inserted

    def ensure_companies(self) -> int:
        """会社データ確保"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {self.config['database']}.companies")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # デフォルト会社作成
                company_data = [{
                    'name': 'Tech0 Sample Company',
                    'created_at': datetime.now() - timedelta(days=365*2),
                    'updated_at': datetime.now()
                }]
                self.bulk_insert('companies', company_data)
                self.stats['companies'] = 1
                return 1
            else:
                logger.info(f"既存の会社: {count}件")
                return count
                
        except Error as e:
            logger.error(f"会社データ確認失敗: {e}")
            return 1
        finally:
            cursor.close()

    def generate_users_employees(self):
        """ユーザー・従業員データ生成（スキーマ準拠）"""
        logger.info(f"ユーザー・従業員データ生成開始: {self.employees_count}件")
        
        company_count = self.ensure_companies()
        
        cursor = self.connection.cursor()
        try:
            # フェーズ1: Users 生成
            logger.info("フェーズ1: Users テーブル投入")
            users_sql = """
                INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    hashed_password=VALUES(hashed_password),
                    full_name=VALUES(full_name),
                    is_active=VALUES(is_active)
            """
            
            users_data = []
            start_date = datetime.now() - timedelta(days=365*2)
            
            for i in range(1, self.employees_count + 1):
                is_active = i <= self.active_employees
                days_offset = random.randint(30, 730) if is_active else random.randint(0, 90)
                created_at = start_date + timedelta(days=days_offset)
                
                # パスワードハッシュ生成
                plain_password = f"password{i:06d}"
                hashed_password = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()
                
                users_data.append((
                    f'user{i:06d}@example.com',       # email
                    hashed_password,                   # hashed_password
                    f'田中 太郎{i:04d}',               # full_name
                    is_active,                         # is_active
                    False,                            # is_superuser
                    created_at                        # created_at
                ))
            
            # バッチ挿入
            batch_size = 1000
            for i in tqdm(range(0, len(users_data), batch_size), desc="Inserting users"):
                batch = users_data[i:i + batch_size]
                cursor.executemany(users_sql, batch)
                if i % (batch_size * 5) == 0:
                    self.connection.commit()
            
            self.connection.commit()
            self.stats['users'] = len(users_data)
            logger.info(f"Users 投入完了: {len(users_data)}件")
            
            # フェーズ2: Employees 生成（user_idを取得して整合性確保）
            logger.info("フェーズ2: Employees テーブル投入")
            
            # 挿入されたuser_idを取得
            cursor.execute("SELECT id, email FROM users ORDER BY id")
            user_mappings = cursor.fetchall()
            
            employees_sql = """
                INSERT INTO employees (user_id, company_id, department, employee_code, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    company_id=VALUES(company_id),
                    department=VALUES(department)
            """
            
            employees_data = []
            for idx, (user_id, email) in enumerate(user_mappings[:self.employees_count]):
                created_at = start_date + timedelta(days=random.randint(30, 730))
                
                employees_data.append((
                    user_id,                                        # user_id (FK)
                    random.randint(1, company_count),              # company_id
                    random.choice(['営業部', '開発部', '管理部', '人事部', '経理部']),  # department
                    f'EMP{user_id:06d}',                           # employee_code (UNIQUE)
                    created_at                                     # created_at
                ))
            
            # バッチ挿入
            for i in tqdm(range(0, len(employees_data), batch_size), desc="Inserting employees"):
                batch = employees_data[i:i + batch_size]
                cursor.executemany(employees_sql, batch)
                if i % (batch_size * 5) == 0:
                    self.connection.commit()
            
            self.connection.commit()
            self.stats['employees'] = len(employees_data)
            logger.info(f"Employees 投入完了: {len(employees_data)}件")
            
        except Error as e:
            logger.error(f"ユーザー・従業員生成失敗: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def generate_energy_records(self):
        """エネルギー使用記録生成（IoTデバイススキーマ準拠）"""
        logger.info(f"エネルギー記録生成開始: {self.active_employees}人 × {self.months_back}ヶ月")
        
        # アクティブユーザーIDを取得
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT id FROM users WHERE is_active = 1 ORDER BY id")
            active_user_ids = [row[0] for row in cursor.fetchall()]
            
            if not active_user_ids:
                logger.warning("アクティブユーザーが見つかりません。エネルギー記録をスキップ")
                return
                
            logger.info(f"フェーズ3: Energy Records テーブル投入（{len(active_user_ids)}名）")
            
            energy_sql = """
                INSERT INTO energy_records (`timestamp`, user_id, energy_consumed, energy_produced, 
                                          grid_import, grid_export, power, temperature, efficiency, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    energy_consumed=VALUES(energy_consumed),
                    power=VALUES(power)
            """
            
            energy_data = []
            base_date = datetime.now().replace(day=1, hour=12, minute=0, second=0, microsecond=0)
            
            for user_id in active_user_ids[:self.active_employees]:
                # 個人の基本消費量パターン
                base_consumption = max(5.0, random.gauss(15.0, 3.0))  # kW平均
                base_production = max(0.0, random.gauss(2.0, 1.0))    # 太陽光等
                
                for month_offset in range(self.months_back):
                    # 月次の代表的なタイムスタンプを生成（月初）
                    target_datetime = base_date - timedelta(days=30 * month_offset)
                    month = target_datetime.month
                    
                    # 季節性適用
                    seasonal_factor = self.seasonal_factors[month]
                    noise = random.gauss(1.0, 0.1)
                    
                    # IoT想定の値を生成
                    consumed = round(base_consumption * seasonal_factor * noise, 2)
                    produced = round(base_production * seasonal_factor * noise * 0.7, 2)  # 日照条件
                    grid_import = round(max(0, consumed - produced), 2)
                    grid_export = round(max(0, produced - consumed) * 0.8, 2)  # 売電効率
                    power = round(consumed * 1000, 1)  # W単位
                    temp = round(20 + 15 * math.sin((month - 1) * math.pi / 6), 1)  # 気温概算
                    efficiency = round(85 + random.gauss(0, 5), 1)  # 効率%
                    
                    energy_data.append((
                        target_datetime,          # timestamp (NOT NULL)
                        user_id,                  # user_id
                        consumed,                 # energy_consumed
                        produced,                 # energy_produced
                        grid_import,              # grid_import
                        grid_export,              # grid_export
                        power,                    # power
                        temp,                     # temperature
                        efficiency,               # efficiency
                        'normal',                 # status
                        target_datetime           # created_at
                    ))
            
            # バッチ挿入
            batch_size = 1000
            for i in tqdm(range(0, len(energy_data), batch_size), desc="Inserting energy records"):
                batch = energy_data[i:i + batch_size]
                cursor.executemany(energy_sql, batch)
                if i % (batch_size * 5) == 0:
                    self.connection.commit()
            
            self.connection.commit()
            self.stats['energy_records'] = len(energy_data)
            logger.info(f"Energy Records 投入完了: {len(energy_data)}件")
            
        except Error as e:
            logger.error(f"エネルギー記録生成失敗: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def generate_rewards(self):
        """景品データ生成（スキーマ準拠）"""
        logger.info("フェーズ4: Rewards テーブル投入")
        
        cursor = self.connection.cursor()
        try:
            rewards_sql = """
                INSERT INTO rewards (title, description, category, stock, points_required, active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    stock=VALUES(stock),
                    points_required=VALUES(points_required),
                    active=VALUES(active)
            """
            
            current_time = datetime.now()
            rewards_data = [
                ('Amazonギフト券 500円', 'Amazon.co.jpで使える500円分のギフト券', 'ギフトカード', 10000, 500, True, current_time),
                ('Amazonギフト券 1000円', 'Amazon.co.jpで使える1000円分のギフト券', 'ギフトカード', 5000, 1000, True, current_time),
                ('スターバックスカード 500円', 'スターバックスで使える500円分のプリペイドカード', 'ギフトカード', 3000, 550, True, current_time),
                ('図書カード 1000円', '全国の書店で使える1000円分の図書カード', 'ギフトカード', 2000, 1100, True, current_time),
                ('QUOカード 500円', 'コンビニ等で使える500円分のQUOカード', 'ギフトカード', 8000, 550, True, current_time),
                ('コーヒー豆（200g）', 'オーガニックコーヒー豆200g', '食品・飲料', 1500, 400, True, current_time),
                ('緑茶ティーバッグセット', '静岡県産緑茶ティーバッグ50個入り', '食品・飲料', 2000, 300, True, current_time),
                ('エコバッグ', '折りたたみ可能なオーガニックコットンエコバッグ', '生活用品', 5000, 200, True, current_time),
                ('マイボトル（500ml）', '保温保冷機能付きステンレスボトル', '生活用品', 1000, 600, True, current_time),
                ('LED電球（60W相当）', '省エネLED電球 昼白色', '生活用品', 3000, 250, True, current_time),
                ('ワイヤレスマウス', 'エルゴノミクスワイヤレスマウス', '電子機器', 500, 800, True, current_time),
                ('モバイルバッテリー', '10000mAh大容量モバイルバッテリー', '電子機器', 800, 1200, True, current_time),
                ('Netflix ギフト券 1ヶ月', 'Netflix 1ヶ月間視聴ギフトコード', 'エンターテイメント', 2000, 900, True, current_time),
                ('映画鑑賞券', '全国の映画館で使える映画鑑賞券', 'エンターテイメント', 1000, 1500, True, current_time),
                ('植物栽培キット', 'ハーブ栽培キット（バジル・パセリ）', 'その他', 1200, 450, True, current_time),
            ]
            
            cursor.executemany(rewards_sql, rewards_data)
            self.connection.commit()
            self.stats['rewards'] = len(rewards_data)
            logger.info(f"Rewards 投入完了: {len(rewards_data)}件")
            
        except Error as e:
            logger.error(f"景品データ生成失敗: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def generate_points_and_redemptions(self):
        """ポイント・交換履歴生成（整合性保証）"""
        logger.info("フェーズ5: Points & Redemptions テーブル投入（スキップ）")
        
        # 既存のポイントシステムテーブルが存在するかチェック
        cursor = self.connection.cursor()
        try:
            cursor.execute("SHOW TABLES LIKE 'points_ledger'")
            if cursor.fetchone():
                logger.info("Points/Redemptions システムは既存テーブルを使用")
                logger.info("必要に応じて app/seeds/ の専用スクリプトを実行してください")
                self.stats['points_ledger'] = 0
                self.stats['redemptions'] = 0
            else:
                logger.warning("Points/Redemptions テーブルが見つかりません（スキップ）")
                
        except Error as e:
            logger.warning(f"ポイントテーブルチェック失敗: {e}")
        finally:
            cursor.close()

    def generate_current_points(self):
        """現在ポイント残高テーブル更新"""
        logger.info("フェーズ6: Points 残高集計（スキップ）")
        logger.info("ポイントシステムは app/seeds/ で管理されます")

    def run_seed(self):
        """シード実行"""
        logger.info("=== Azure MySQL ダミーデータ生成開始 ===")
        logger.info(f"対象: 従業員{self.employees_count}人、アクティブ{self.active_employees}人、期間{self.months_back}ヶ月")
        
        if not self.connect():
            return False
            
        try:
            # スキーマ読み込み
            self.load_schemas()
            
            # データ生成実行
            logger.info("1. 会社データ確保")
            self.ensure_companies()
            
            logger.info("2. ユーザー・従業員生成")  
            self.generate_users_employees()
            
            logger.info("3. エネルギー記録生成")
            self.generate_energy_records()
            
            logger.info("4. 報酬生成")
            self.generate_rewards()
            
            logger.info("5. ポイント・交換履歴生成")
            self.generate_points_and_redemptions()
            
            logger.info("6. ポイント残高集計")
            self.generate_current_points()
            
            # 統計出力
            elapsed = datetime.now() - self.start_time
            logger.info("=== 生成完了 ===")
            logger.info(f"所要時間: {elapsed}")
            logger.info("生成件数:")
            for table, count in self.stats.items():
                logger.info(f"  {table}: {count:,}件")
                
            return True
            
        except Exception as e:
            logger.error(f"データ生成中にエラー: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            if self.connection:
                self.connection.close()

def main():
    # 環境変数読み込み
    load_dotenv()
    
    # CLI引数
    parser = argparse.ArgumentParser(description='Azure MySQL ダミーデータ生成')
    parser.add_argument('--employees', type=int, default=15000, help='従業員数')
    parser.add_argument('--months', type=int, default=24, help='過去データ期間（月）')
    parser.add_argument('--active-rate', type=float, default=0.6, help='アクティブ率')
    args = parser.parse_args()
    
    # データベース設定
    config = {
        'host': os.getenv('MYSQL_HOST', 'rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'tech0gen10student'), 
        'password': os.getenv('MYSQL_PASSWORD'),
        'database': os.getenv('MYSQL_DB', 'test_tanaka'),
        'ssl_ca': os.getenv('MYSQL_SSL_CA', './DigiCertGlobalRootCA.crt.pem'),
        'employees': args.employees,
        'months': args.months,
        'active_rate': args.active_rate
    }
    
    if not config['password']:
        logger.error("MYSQL_PASSWORD環境変数が設定されていません")
        sys.exit(1)
    
    # 実行
    seeder = DatabaseSeeder(config)
    success = seeder.run_seed()
    
    if success:
        logger.info("✅ ダミーデータ生成完了！")
        sys.exit(0)
    else:
        logger.error("❌ ダミーデータ生成失敗")
        sys.exit(1)

if __name__ == '__main__':
    main()