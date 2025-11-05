from pymilvus import db, utility, milvus_client, connections

def del_all():

    conn = connections.connect(host="127.0.0.1", port=19530)
    database_list = db.list_database()


    for i in database_list:
        conn = connections.connect(host="127.0.0.1", port=19530, db_name=i)
        colist = utility.list_collections()
        for j in colist:
            utility.drop_collection(collection_name=j)
        
        
    for i in database_list:
        if i=='default':
            continue
        db.drop_database(db_name=i)
        