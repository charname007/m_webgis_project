package com.backend.be.mapper;

import java.util.List;
import java.util.Map;

import org.apache.ibatis.annotations.Mapper;

import com.backend.be.model.FieldQueryRequest;
import com.backend.be.model.SpatialExtentRequest;
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
    String getSpatialTableGeojsonByExtent(String tableName, SpatialExtentRequest request);
    
    /**
     * 根据字段条件查询空间表要素并返回 GeoJSON
     * @param request 字段查询请求
     * @return GeoJSON 格式的要素集合
     */
    String getSpatialTableGeojsonByFields(FieldQueryRequest request);
}
