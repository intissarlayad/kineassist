import os
import sys
from pathlib import Path

# Load secrets from .streamlit/secrets.toml if present (local dev)
secrets_path = Path('.streamlit') / 'secrets.toml'
if secrets_path.is_file():
    try:
        import toml
        sec = toml.load(secrets_path)
        os.environ.update({k: str(v) for k, v in sec.items()})
    except Exception as e:
        print('⚠️ Could not load secrets.toml:', e)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print('❌ DATABASE_URL not set. Ensure it is in environment or .streamlit/secrets.toml')
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError as e:
    print('❌ psycopg2 is not installed. Run: pip install psycopg2-binary')
    sys.exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute('SELECT version();')
    result = cur.fetchone()
    print('✅ Connection successful. PostgreSQL version:', result)
    conn.close()
except Exception as e:
    print('❌ Connection failed:', e)
    sys.exit(1)