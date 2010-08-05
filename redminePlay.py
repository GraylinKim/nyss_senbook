from MySQLdb import connect
from MySQLdb.cursors import DictCursor

from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint


def get_connection():
    return connect(
        "127.0.0.1",
        "senbook",
        "S3nb00k!",
        "redmine",
        port=3305,
        cursorclass=DictCursor,
        connect_timeout=10)
        
def query_dict(conn,query):
    c = conn.cursor()
    c.execute(query)
    return c.fetchall()

def query_list(conn,query):
    c = conn.cursor()
    c.execute(query)
    return [r.values() for r in c.fetchall()]
    
mysql = get_connection()

"   SELECT                                                  \
        roles.name AS role,                                 \
        members.created_on AS since,                        \
        projects.name AS project_name                       \
    FROM users                                              \
        JOIN members on users.id=members.user_id            \
        JOIN roles on members.role_id=roles.id              \
        JOIN projects on members.project_id=projects.id     \
    WHERE                                                   \
        firstname='Andrew' and lastname='Hoppin'"
