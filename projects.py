from settings import settings

"""
Save everything to couchdb all the time, have real time updates override its data though during construction.
This lets us work even when data sources are disabled and/or down or w/e.
"""
class Project(object):

    def __init__(self,name):
        
        data = dict()
        defaults = dict()
        
        if 'mysql' in settings:
            mysql = settings['mysql'].connect()
            
            results = mysql.query("""
                SELECT
                    projects.name AS name,
                    projects.created_on AS created,
                    projects.updated_on AS updated,
                    projects.description AS description,
                    news.title AS news_title,
                    news.id AS news_id,
                    news.summary AS news_summary,
                    news.description AS news_description,
                    news.created_on AS news_date,
                    newsauthor.firstname AS news_author_firstname,
                    newsauthor.lastname AS news_author_lastname,
                    users.firstname AS member_firstname,
                    users.lastname AS member_lastname,
                    members.id AS member_id,
                    members.created_on AS member_since,
                    roles.name AS member_role,
                    subprojects.id AS subproject_id,
                    subprojects.name AS subproject_name,
                    subprojects.created_on AS subproject_started,
                    subprojects.updated_on AS subproject_updated,
                    parentproject.name AS parentproject_name,
                    parentproject.created_on AS parentproject_started,
                    parentproject.updated_on AS parentproject_updated
                FROM projects
                    LEFT JOIN members ON members.project_id=projects.id
                    LEFT JOIN news ON news.project_id=projects.id
                    LEFT JOIN users ON members.user_id=users.id
                    LEFT JOIN roles ON members.role_id=roles.id
                    LEFT JOIN projects AS subprojects ON projects.id=subprojects.parent_id
                    LEFT JOIN projects AS parentproject ON projects.parent_id=parentproject.id
                    LEFT JOIN users AS newsauthor ON newsauthor.id=news.author_id
                WHERE 
                    projects.name=%s
            """,(name))
            
            
            """ Thar be black magic here. Don't touch for any reason. """
            mysql_data = dict(
                name=results[0]['name'],
                description=results[0]['description'],
                created=results[0]['created'],
                updated=results[0]['updated'],
                parentproject=dict(
                        name=results[0]['parentproject_name'],
                        started=results[0]['parentproject_started'],
                        updated=results[0]['parentproject_updated']
                    ),
                childprojects=dict([
                        [
                            row['subproject_id'],
                            dict(
                                name=row['subproject_name'],
                                started=row['subproject_started'],
                                updated=row['subproject_updated'],
                            )
                        ] for row in results if row['subproject_name']!=None
                    ]).values(),
                newsitems=reversed(dict([
                        [
                            row['news_id'],dict(
                                started=row['news_date'],
                                title=row['news_title'],
                                author="%s %s" % (row['news_author_firstname'],row['news_author_lastname']),
                                summary=row['news_summary'],
                                description=row['news_description'],
                            )
                        ] for row in results if row['news_title']!=None
                    ]).values()),
                members=dict([
                        [
                            row['member_id'], dict(
                                role=row['member_role'],
                                name="%s %s" % (row['member_firstname'],row['member_lastname']),
                                since=row['member_since'],
                            )
                        ] for row in results
                    ]).values(),   
            )
            """ End of Black Magic """
            
            data = dict( mysql_data.items()+data.items() )
        else:
            print "mysql not enabled"
            
        self.data = dict( defaults.items()+data.items() )
