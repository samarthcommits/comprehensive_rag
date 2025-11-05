import sqlite3
from pymilvus import db, utility, connections

import os
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from delete_data import del_all
class CollectionDatabase:

    def __init__(self, db_path: str = "collections_metadata.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._create_table()
    
    def _create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                parent_collection TEXT NOT NULL,
                collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT NOT NULL,
                user_name TEXT NOT NULL,
                retrieval_technique TEXT NOT NULL,
                database_type TEXT NOT NULL,
                chunking_strategy TEXT NOT NULL,
                pdf_name TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(collection_name, user_name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def insert_collection(
        self, 
        collection_name: str, 
        user_name: str, 
        retrieval_technique: str,
        database_type: str,
        chunking_strategy: str,
        parent_name = 'testing',
        pdf_name = ''
    ) -> bool:
        """
        Insert a new collection record or update if exists.
        
        Args:
            collection_name: Name of the collection
            user_name: Username/database name
            retrieval_technique: Type of retrieval technique used
            database_type: Type of database (e.g., 'MilvusDB')
            chunking_strategy: Chunking strategy used (e.g., 'Recursive', 'Semantic')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Use INSERT OR REPLACE to handle duplicates
            cursor.execute("""
                INSERT OR REPLACE INTO collections 
                (parent_collection, collection_name, user_name, retrieval_technique, database_type, chunking_strategy, pdf_name, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (parent_name, collection_name, user_name, retrieval_technique, database_type, chunking_strategy, pdf_name, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error inserting collection: {str(e)}")
            return False
    
    def get_collection_info(
        self, 
        collection_name: str, 
        user_name: str
    ) -> Optional[Dict[str, str]]:
        """
        Retrieve collection information.
        
        Args:
            collection_name: Name of the collection
            user_name: Username/database name
            
        Returns:
            Dict with collection info or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT collection_id, collection_name, user_name, retrieval_technique, 
                       database_type, chunking_strategy, created_at, updated_at, pdf_name
                FROM collections
                WHERE collection_name = ? AND user_name = ?
            """, (collection_name, user_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'collection_id': result[0],
                    'collection_name': result[1],
                    'user_name': result[2],
                    'retrieval_technique': result[3],
                    'database_type': result[4],
                    'chunking_strategy': result[5],
                    'created_at': result[6],
                    'updated_at': result[7],
                    'pdf_name': result[8]
                }
            return None
            
        except Exception as e:
            print(f"Error retrieving collection info: {str(e)}")
            return None
    
    def get_parent_collection(self, parent_name = ''):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT parent_collection, collection_id, collection_name, user_name, retrieval_technique, 
                       database_type, chunking_strategy, created_at, updated_at
                FROM collections
                WHERE parent_collection = ?
            """, (parent_name))
            
            result = cursor.fetchall()
            conn.close()

        except Exception as e:
            print(f"Error retrieving collection info: {str(e)}")
            return None

    def get_all_parent_collections(self, username = ''):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT parent_collection
                FROM collections
                WHERE user_name = ?
            """, (username,))
            
            result = cursor.fetchall()
            # for row in result:
            res = [row[0] for row in result]
            conn.close()
            return res

        except Exception as e:
            print(f"Error retrieving collection info: {str(e)}")
            return None
                  
    def get_all_collections_for_user(self, user_name: str) -> List[Dict[str, str]]:
        """
        Get all collections for a specific user.
        
        Args:
            user_name: Username/database name
            
        Returns:
            List of dictionaries containing collection info
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT collection_id, collection_name, user_name, retrieval_technique,
                       database_type, chunking_strategy, created_at, updated_at
                FROM collections
                WHERE user_name = ?
                ORDER BY updated_at DESC
            """, (user_name,))
            
            results = cursor.fetchall()
            conn.close()
            
            collections = []
            for row in results:
                collections.append({
                    'collection_id': row[0],
                    'collection_name': row[1],
                    'user_name': row[2],
                    'retrieval_technique': row[3],
                    'database_type': row[4],
                    'chunking_strategy': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                })
            
            return collections
            
        except Exception as e:
            print(f"Error retrieving collections: {str(e)}")
            return []
    
    def collection_exists(self, collection_name: str, user_name: str) -> bool:
        """
        Check if a collection exists.
        
        Args:
            collection_name: Name of the collection
            user_name: Username/database name
            
        Returns:
            bool: True if exists, False otherwise
        """
        result = self.get_collection_info(collection_name, user_name)
        return result is not None
    
    def delete_collection(self, collection_name: str, user_name: str) -> bool:
        """
        Delete a collection record.
        
        Args:
            collection_name: Name of the collection
            user_name: Username/database name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM collections
                WHERE collection_name = ? AND user_name = ?
            """, (collection_name, user_name))
            
            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()
            
            return rows_affected > 0
            
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
            return False
    
    def get_all_collections(self) -> List[Dict[str, str]]:
        """
        Get all collections in the database.
        
        Returns:
            List of dictionaries containing collection info
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT collection_id, collection_name, user_name, retrieval_technique,
                       database_type, chunking_strategy, created_at, updated_at
                FROM collections
                ORDER BY updated_at DESC
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            collections = []
            for row in results:
                collections.append({
                    'collection_id': row[0],
                    'collection_name': row[1],
                    'user_name': row[2],
                    'retrieval_technique': row[3],
                    'database_type': row[4],
                    'chunking_strategy': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                })
            
            return collections
            
        except Exception as e:
            print(f"Error retrieving all collections: {str(e)}")
            return []
        
    def delete_all(self):
        try:
            del_all()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM collections""")
            conn.commit()
            conn.commit()
        except Exception as e:
            print(f"Error truncating collections: {str(e)}")
            return None

class UserDatabase:
    def __init__(self, db_path: str = "collections_metadata.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._create_table()


    def _create_table(self):
        """Create the Users table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_name, password)
            )
        """)
        
        conn.commit()
        conn.close()

    def insert_user(
        self, 
        user_name: str, 
        password: str,
    ) -> bool:
        conn = connections.connect(host="127.0.0.1", port=19530)
        # user_name = st.session_state.username
        database_list = db.list_database()
        if len(user_name)>0:
            if user_name not in database_list:
                db.create_database(db_name=user_name)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Use INSERT OR REPLACE to handle duplicates
            cursor.execute("""
                INSERT OR REPLACE INTO Users 
                (user_name, password, updated_at)
                VALUES (?, ?, ?)
            """, (user_name, password, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error inserting collection: {str(e)}")
            return False
        
    def get_user_name_info(
        self, 
        user_name: str,
    ) -> Optional[Dict[str, str]]:
   
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, user_name, created_at, updated_at
                FROM Users
                WHERE user_name = ?
            """, (user_name,))
            
            result = cursor.fetchall()
            conn.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'user_name': result[1],
                    'created_at': result[2],
                    'updated_at': result[3]
                }
            return None
            
        except Exception as e:
        
            print(f"Error retrieving username info: {str(e)}")
            return None
        
    def validate_user(
        self, 
        user_name: str,
        password: str
    ) -> Optional[Dict[str, str]]:
       
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, user_name, created_at, updated_at, password
                FROM Users
                WHERE user_name = ? AND password = ?
            """, (user_name, password))
            
            result = cursor.fetchall()
            conn.close()
            
            if result:
                try:
                    result = result[0]
                    return True
                except:
                    return False
            return False
            
        except Exception as e:
            print(f"Error validating user: {str(e)}")
            return None
    
    def delete_all(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""DELETE FROM Users""")
            conn.commit()
            conn.close()

        except Exception as e:
            
            print(f"Error truncating Users: {str(e)}")
            return None
    