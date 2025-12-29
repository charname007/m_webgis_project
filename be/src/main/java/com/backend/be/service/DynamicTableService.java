package com.backend.be.service;
import java.util.List;
import java.util.Map;

import com.backend.be.model.FieldQueryRequest;
import com.backend.be.model.SpatialExtentRequest;
import com.backend.be.model.SpatialTableRequest;

public interface DynamicTableService {
    List<String> getAllTableNames();
    List<Map<String, Object>> getTableData(String tableName);
    List<Map<String, Object>> getTableSchema(String tableName);
    List<String> getSpatialTables();
    String getSpatialTablesGeojson(SpatialTableRequest request);
    String getSpatialTableGeojsonByExtent(String tableName, SpatialExtentRequest request);
    
    /**
     * 根据字段条件查询空间表要素并返回 GeoJSON
     * @param request 字段查询请求
     * @return GeoJSON 格式的要素集合
     */
    String getSpatialTableGeojsonByFields(FieldQueryRequest request);
}
