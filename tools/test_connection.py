import os, mysql.connector
from dotenv import load_dotenv
load_dotenv()
cfg = {
  "host": os.getenv("MYSQL_HOST"),
  "port": int(os.getenv("MYSQL_PORT", "3306")),
  "user": os.getenv("MYSQL_USER"),
  "password": os.getenv("MYSQL_PASSWORD"),
  "database": os.getenv("MYSQL_DATABASE"),
  "ssl_ca": os.getenv("MYSQL_SSL_CA"),
}
print("Connecting with:", {k: cfg[k] for k in cfg if k != "password"})
cn = mysql.connector.connect(
    host=cfg["host"], port=cfg["port"],
    user=cfg["user"], password=cfg["password"],
    database=cfg["database"], ssl_ca=cfg["ssl_ca"]
)
cur = cn.cursor()
cur.execute("SELECT DATABASE(), VERSION()")
print("OK:", cur.fetchone())
cur.close(); cn.close()