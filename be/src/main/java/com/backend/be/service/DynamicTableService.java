package com.backend.be.service;
import java.util.List;
import java.util.Map;
public interface DynamicTableService {
    List<String> getAllTableNames();
    List<Map<String, Object>> getTableData(String tableName);
    List<Map<String, Object>> getTableSchema(String tableName);
    List<String> getSpatialTables();
    
}
