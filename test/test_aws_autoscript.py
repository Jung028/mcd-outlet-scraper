import paramiko

# SSH Configuration
EC2_HOST = "ec2-3-27-228-44.ap-southeast-2.compute.amazonaws.com"
SSH_KEY_PATH = r"C:\Users\AdamLim\Downloads\ec2-database-connect.pem"
SSH_USER = "ec2-user"

# PostgreSQL Configuration
DB_HOST = "database-test1.cpgsc4aw269b.ap-southeast-2.rds.amazonaws.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "Remember121314"  # 🚨 Keep this secure!

# SQL command to create a simple table
SQL_COMMAND = """
CREATE TABLE IF NOT EXISTS test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# PostgreSQL command with auto-login
PSQL_COMMAND = f'PGPASSWORD="{DB_PASSWORD}" psql --host={DB_HOST} --port={DB_PORT} --dbname={DB_NAME} --username={DB_USER} -c "{SQL_COMMAND}"'

def connect_via_ssh():
    """ Establish SSH connection and run PostgreSQL command """
    print("🔄 Connecting to EC2 instance via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(EC2_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)
        print("✅ SSH connection established.")

        # Execute the PostgreSQL command to create a table
        print("🔄 Running SQL command...")
        stdin, stdout, stderr = ssh.exec_command(PSQL_COMMAND)

        # Read and print output
        output = stdout.read().decode()
        error = stderr.read().decode()

        if output:
            print(f"✅ SQL Output:\n{output}")
        if error:
            print(f"❌ SQL Error:\n{error}")

    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    connect_via_ssh()
