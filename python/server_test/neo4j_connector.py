from langchain_neo4j import Neo4jGraph

class neo4j_connector:
    def __init__(self, url, user, password):
        self.graph = Neo4jGraph(url=url, username=user, password=password)

    def run_query(self, query):
        return self.graph.query(query)
    def close(self):
        self.graph.close()
    
    def refresh_graph(self):
        self.graph.refresh_schema()
    
    def get_schema(self):
        return self.graph.schema
    def get_graph(self):
        return self.graph