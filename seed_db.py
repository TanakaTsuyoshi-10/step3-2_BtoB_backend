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
except ImportError as e:
    print(f"必要なライブラリがインストールされていません: {e}")
    print("pip install -r requirements.txt を実行してください")
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
        """ユーザー・従業員データ生成"""
        logger.info(f"ユーザー・従業員データ生成開始: {self.employees_count}件")
        
        company_count = self.ensure_companies()
        users_data = []
        employees_data = []
        
        # 作成日の分散
        start_date = datetime.now() - timedelta(days=365*2)
        
        for i in range(1, self.employees_count + 1):
            # アクティブ判定
            is_active = i <= self.active_employees
            
            # 作成日（アクティブユーザーは古いユーザーほど多い）
            if is_active:
                days_offset = random.randint(30, 730)  # 1ヶ月〜2年前
            else:
                days_offset = random.randint(0, 90)   # 最近作成が多い
                
            created_at = start_date + timedelta(days=days_offset)
            
            # ユーザーデータ
            user_data = {
                'email': f'user{i:06d}@example.com',
                'password_hash': 'dummy_hash_' + str(i),
                'first_name': f'太郎{i:04d}',
                'last_name': f'田中',
                'is_active': is_active,
                'created_at': created_at,
                'updated_at': created_at
            }
            
            # 従業員データ
            employee_data = {
                'user_id': i,  # auto_incrementを仮定
                'company_id': random.randint(1, company_count),
                'employee_id': f'EMP{i:06d}',
                'department': random.choice(['営業部', '開発部', '管理部', '人事部', '経理部']),
                'position': random.choice(['一般', '主任', '係長', '課長', '部長']),
                'created_at': created_at,
                'updated_at': created_at
            }
            
            users_data.append(user_data)
            employees_data.append(employee_data)
        
        # バルクINSERT
        self.stats['users'] = self.bulk_insert('users', users_data)
        self.stats['employees'] = self.bulk_insert('employees', employees_data)

    def generate_energy_records(self):
        """エネルギー使用記録生成"""
        logger.info(f"エネルギー記録生成開始: {self.active_employees}人 × {self.months_back}ヶ月")
        
        energy_data = []
        base_date = datetime.now().replace(day=1)
        
        # 電気・ガス単価
        electricity_rate = 30  # 円/kWh
        gas_rate = 160        # 円/m³
        
        for user_id in range(1, self.active_employees + 1):
            # 個人の基本使用量（正規分布）
            base_electricity = max(200, random.gauss(450, 100))  # kWh
            base_gas = max(10, random.gauss(35, 8))              # m³
            
            for month_offset in range(self.months_back):
                target_date = base_date - timedelta(days=30 * month_offset)
                month = target_date.month
                year = target_date.year
                
                # 季節性適用
                seasonal_factor = self.seasonal_factors[month]
                noise = random.gauss(1.0, 0.1)  # ±10%ノイズ
                
                # 電気記録
                electricity_usage = base_electricity * seasonal_factor * noise
                electricity_cost = electricity_usage * electricity_rate
                
                energy_data.append({
                    'user_id': user_id,
                    'type': 'electricity',
                    'year': year,
                    'month': month,
                    'usage_value': round(electricity_usage, 2),
                    'unit': 'kWh',
                    'cost_yen': round(electricity_cost),
                    'created_at': target_date
                })
                
                # ガス記録（70%の確率）
                if random.random() < 0.7:
                    gas_usage = base_gas * seasonal_factor * noise
                    gas_cost = gas_usage * gas_rate
                    
                    energy_data.append({
                        'user_id': user_id,
                        'type': 'gas',
                        'year': year,
                        'month': month,
                        'usage_value': round(gas_usage, 2),
                        'unit': 'm³',
                        'cost_yen': round(gas_cost),
                        'created_at': target_date
                    })
        
        self.stats['energy_records'] = self.bulk_insert('energy_records', energy_data)

    def generate_rewards(self):
        """景品データ生成"""
        logger.info("景品データ生成開始")
        
        rewards_data = [
            {'name': 'Amazonギフト券 500円', 'category': 'ギフトカード', 'points_required': 500, 'stock': 10000, 'description': 'Amazon.co.jpで使える500円分のギフト券'},
            {'name': 'Amazonギフト券 1000円', 'category': 'ギフトカード', 'points_required': 1000, 'stock': 5000, 'description': 'Amazon.co.jpで使える1000円分のギフト券'},
            {'name': 'スターバックスカード 500円', 'category': 'ギフトカード', 'points_required': 550, 'stock': 3000, 'description': 'スターバックスで使える500円分のプリペイドカード'},
            {'name': '図書カード 1000円', 'category': 'ギフトカード', 'points_required': 1100, 'stock': 2000, 'description': '全国の書店で使える1000円分の図書カード'},
            {'name': 'QUOカード 500円', 'category': 'ギフトカード', 'points_required': 550, 'stock': 8000, 'description': 'コンビニ等で使える500円分のQUOカード'},
            {'name': 'コーヒー豆（200g）', 'category': '食品・飲料', 'points_required': 400, 'stock': 1500, 'description': 'オーガニックコーヒー豆200g'},
            {'name': '緑茶ティーバッグセット', 'category': '食品・飲料', 'points_required': 300, 'stock': 2000, 'description': '静岡県産緑茶ティーバッグ50個入り'},
            {'name': 'エコバッグ', 'category': '生活用品', 'points_required': 200, 'stock': 5000, 'description': '折りたたみ可能なオーガニックコットンエコバッグ'},
            {'name': 'マイボトル（500ml）', 'category': '生活用品', 'points_required': 600, 'stock': 1000, 'description': '保温保冷機能付きステンレスボトル'},
            {'name': 'LED電球（60W相当）', 'category': '生活用品', 'points_required': 250, 'stock': 3000, 'description': '省エネLED電球 昼白色'},
            {'name': 'ワイヤレスマウス', 'category': '電子機器', 'points_required': 800, 'stock': 500, 'description': 'エルゴノミクスワイヤレスマウス'},
            {'name': 'モバイルバッテリー', 'category': '電子機器', 'points_required': 1200, 'stock': 800, 'description': '10000mAh大容量モバイルバッテリー'},
            {'name': 'Netflix ギフト券 1ヶ月', 'category': 'エンターテイメント', 'points_required': 900, 'stock': 2000, 'description': 'Netflix 1ヶ月間視聴ギフトコード'},
            {'name': '映画鑑賞券', 'category': 'エンターテイメント', 'points_required': 1500, 'stock': 1000, 'description': '全国の映画館で使える映画鑑賞券'},
            {'name': '植物栽培キット', 'category': 'その他', 'points_required': 450, 'stock': 1200, 'description': 'ハーブ栽培キット（バジル・パセリ）'},
        ]
        
        # created_at, updated_atを追加
        current_time = datetime.now()
        for reward in rewards_data:
            reward['created_at'] = current_time
            reward['updated_at'] = current_time
            reward['active'] = True
        
        self.stats['rewards'] = self.bulk_insert('rewards', rewards_data)

    def generate_points_and_redemptions(self):
        """ポイント・交換履歴生成（整合性保証）"""
        logger.info("ポイント・交換履歴生成開始")
        
        # 報酬一覧取得
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(f"SELECT id, points_required, stock FROM {self.config['database']}.rewards")
        rewards = cursor.fetchall()
        cursor.close()
        
        if not rewards:
            logger.error("報酬データが見つかりません。generate_rewards()を先に実行してください。")
            return
        
        points_ledger_data = []
        redemptions_data = []
        reward_stock_updates = {r['id']: r['stock'] for r in rewards}
        
        # アクティブユーザーの70%がポイント活動
        point_active_users = int(self.active_employees * 0.7)
        
        for user_id in range(1, point_active_users + 1):
            user_balance = 0
            
            # ポイント獲得イベント（月1-3回、過去2年）
            for month_offset in range(self.months_back):
                events_this_month = random.randint(1, 3)
                
                for _ in range(events_this_month):
                    # 獲得ポイント（ログイン、省エネ活動等）
                    points_earned = random.choice([10, 20, 30, 50, 100, 150])
                    event_date = datetime.now() - timedelta(days=30*month_offset + random.randint(0, 29))
                    
                    points_ledger_data.append({
                        'user_id': user_id,
                        'delta': points_earned,
                        'type': 'earn',
                        'reason': random.choice([
                            '月次ログイン',
                            '省エネ目標達成',
                            'データアップロード',
                            'エアコン温度最適化',
                            'LED化推進',
                            '研修受講完了'
                        ]),
                        'created_at': event_date
                    })
                    user_balance += points_earned
            
            # 交換イベント（30%のユーザーが年1-2回）
            if random.random() < 0.3:
                redemption_count = random.randint(1, 2)
                
                for _ in range(redemption_count):
                    # 交換可能な報酬から選択
                    affordable_rewards = [r for r in rewards 
                                        if r['points_required'] <= user_balance 
                                        and reward_stock_updates[r['id']] > 0]
                    
                    if affordable_rewards:
                        reward = random.choice(affordable_rewards)
                        redemption_date = datetime.now() - timedelta(days=random.randint(0, 365))
                        
                        # 在庫減少
                        reward_stock_updates[reward['id']] -= 1
                        user_balance -= reward['points_required']
                        
                        # ポイント消費記録
                        points_ledger_data.append({
                            'user_id': user_id,
                            'delta': -reward['points_required'],
                            'type': 'spend',
                            'reason': f"{reward['id']}番商品と交換",
                            'created_at': redemption_date
                        })
                        
                        # 交換記録
                        redemptions_data.append({
                            'user_id': user_id,
                            'reward_id': reward['id'],
                            'points_used': reward['points_required'],
                            'status': 'completed',
                            'created_at': redemption_date
                        })
        
        # トランザクション開始
        try:
            self.connection.start_transaction()
            
            # ポイント履歴
            self.stats['points_ledger'] = self.bulk_insert('points_ledger', points_ledger_data)
            
            # 交換履歴  
            self.stats['redemptions'] = self.bulk_insert('redemptions', redemptions_data)
            
            # 報酬在庫更新
            cursor = self.connection.cursor()
            for reward_id, new_stock in reward_stock_updates.items():
                cursor.execute(
                    f"UPDATE {self.config['database']}.rewards SET stock = %s WHERE id = %s",
                    (new_stock, reward_id)
                )
            cursor.close()
            
            self.connection.commit()
            logger.info("ポイント・交換データ生成完了（整合性保証）")
            
        except Error as e:
            logger.error(f"ポイント・交換データ生成失敗: {e}")
            self.connection.rollback()
            raise

    def generate_current_points(self):
        """現在ポイント残高テーブル更新"""
        logger.info("現在ポイント残高計算中...")
        
        try:
            cursor = self.connection.cursor()
            
            # points_ledgerから残高集計してpointsテーブルにUPSERT
            sql = f"""
                INSERT INTO {self.config['database']}.points (user_id, current_balance, total_earned, total_spent, updated_at)
                SELECT 
                    user_id,
                    SUM(delta) as current_balance,
                    SUM(CASE WHEN delta > 0 THEN delta ELSE 0 END) as total_earned,
                    SUM(CASE WHEN delta < 0 THEN ABS(delta) ELSE 0 END) as total_spent,
                    NOW() as updated_at
                FROM {self.config['database']}.points_ledger 
                GROUP BY user_id
                ON DUPLICATE KEY UPDATE
                    current_balance = VALUES(current_balance),
                    total_earned = VALUES(total_earned),  
                    total_spent = VALUES(total_spent),
                    updated_at = VALUES(updated_at)
            """
            
            cursor.execute(sql)
            points_count = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            logger.info(f"ポイント残高更新: {points_count}件")
            
        except Error as e:
            logger.error(f"ポイント残高計算失敗: {e}")
            self.connection.rollback()

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