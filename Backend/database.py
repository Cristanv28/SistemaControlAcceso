import pymysql

def get_connection():
    try:
        conn = pymysql.connect(
            host="switchyard.proxy.rlwy.net",
            port=35034,
            user="root",
            password="ayYZvinkilJdcByKNwSgjJQnQakRcSfV",
            database="railway",
            cursorclass=pymysql.cursors.DictCursor
        )

        return conn

    except pymysql.MySQLError as e:
        print("Error de conexión:", e)
        return None


def get_cursor():
    conn = get_connection()

    if conn is None:
        return None, None

    return conn, conn.cursor()