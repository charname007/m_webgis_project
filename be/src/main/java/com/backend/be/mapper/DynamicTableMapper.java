package com.backend.be.mapper;

import java.util.List;
import java.util.Map;
import org.apache.ibatis.annotations.Mapper;

import com.backend.be.model.SpatialTableRequest;

@Mapper
public interface DynamicTableMapper {
    List<String> getAllTableNames();
    boolean tableExists(String tableName);
    List<Map<String, Object>> getTableData(String tableName);
    List<Map<String, Object>> getTableSchema(String tableName);
    List<String> getSpatialTables();
    String getSpatialTableGeojson(String tableName);
    String getSpatialTablesGeojson(SpatialTableRequest request);
}
