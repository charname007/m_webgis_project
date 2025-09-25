from langchain_community.utilities import SQLDatabase
from geoalchemy2 import Geometry


class SQLConnector:
    def __init__(self):
         self.db = SQLDatabase.from_uri("postgresql://sagasama:cznb6666@localhost:5432/WGP_db",engine_args={
   "connect_args": {"application_name": "webgis_project"},
                "echo": True  # 可选：打印 SQL 日志
            })
                                        
         print(self.db.dialect)
         print(self.db.get_usable_table_names())


        