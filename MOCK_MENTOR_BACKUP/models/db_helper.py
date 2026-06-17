# models/db_helper.py

from flask_mysqldb import MySQL

# Create MySQL object
mysql = MySQL()

# Initialize MySQL with app
def init_mysql(app):
    mysql.init_app(app)

# Execute SELECT query and return all rows
def fetch_all(query, params=()):
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return rows

# Execute SELECT query and return one row
def fetch_one(query, params=()):
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()
    return row

# Execute INSERT / UPDATE / DELETE
def execute_query(query, params=()):
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    mysql.connection.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id

# Return rows as dictionaries
def fetch_dict(query, params=()):
    cur = mysql.connection.cursor()
    cur.execute(query, params)

    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    return rows