import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
import snowflake.connector

load_dotenv()

with open(os.path.expanduser(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]), "rb") as f:
    p_key = serialization.load_pem_private_key(f.read(), password=None)

pkb = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    private_key=pkb,
    role=os.environ["SNOWFLAKE_ROLE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    schema=os.environ["SNOWFLAKE_SCHEMA"],
)

cur = conn.cursor()
cur.execute("SELECT CURRENT_VERSION(), CURRENT_ACCOUNT(), CURRENT_WAREHOUSE()")
print(cur.fetchone())
cur.close()
conn.close()
