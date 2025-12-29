package com.backend.be.service.impl;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.backend.be.mapper.SpatialTableMapper;
import com.backend.be.model.FieldQueryRequest;
import com.backend.be.model.SpatialExtentRequest;
import com.backend.be.model.SpatialTableRequest;
import com.backend.be.service.SpatialTableService;

@Service
public class SpatialTableServiceImpl implements SpatialTableService {

    @Autowired
    private SpatialTableMapper tableMapper;

    @Override
    public List<String> getAllTableNames() {
        return tableMapper.getAllTableNames();
    }

    @Override
    public List<Map<String, Object>> getTableData(String tableName) {
        return tableMapper.getTableData(tableName);
    }

    @Override
    public List<Map<String, Object>> getTableSchema(String tableName) {
        return tableMapper.getTableSchema(tableName);
    }

    @Override
    public List<String> getSpatialTables() {
        return tableMapper.getSpatialTables();
    }

    @Override
    public String getSpatialTableGeojson(String tableName) {
        return tableMapper.getSpatialTableGeojson(tableName);
    }

    @Override
    public String getSpatialTablesGeojson(SpatialTableRequest request) {
        return tableMapper.getSpatialTablesGeojson(request);
    }

    @Override
    public String getSpatialTableGeojsonByExtent(String tableName, SpatialExtentRequest request) {
        // 验证表名是否存在
        if (!tableMapper.tableExists(tableName)) {
            throw new IllegalArgumentException("表 '" + tableName + "' 不存在");
        }
        
        // 验证坐标范围合理性
        if (request.getMinLon() >= request.getMaxLon() || request.getMinLat() >= request.getMaxLat()) {
            throw new IllegalArgumentException("坐标范围无效：最小坐标必须小于最大坐标");
        }
        
        // 检查坐标范围是否过大（防止查询整个地球）
        double extentWidth = request.getMaxLon() - request.getMinLon();
        double extentHeight = request.getMaxLat() - request.getMinLat();
        if (extentWidth > 180 || extentHeight > 90) {
            throw new IllegalArgumentException("查询范围过大，请缩小查询范围");
        }
        
        return tableMapper.getSpatialTableGeojsonByExtent(tableName, request);
    }
        @Override
    public String getSpatialTableGeojsonByFields(FieldQueryRequest request) {
        // 验证请求参数
        if (!request.isValid()) {
            throw new IllegalArgumentException("无效的查询请求: " + request.getQueryDescription());
        }
        
        // 验证表名
        validateTableName(request.getTableName());
        
        // 验证字段条件
        if (request.getFieldConditions() == null || request.getFieldConditions().isEmpty()) {
            throw new IllegalArgumentException("字段查询条件不能为空");
        }
        
        // 调用 Mapper 进行字段查询
        try {
            String result = tableMapper.getSpatialTableGeojsonByFields(request);
            System.out.println("字段查询成功 - " + request.getQueryDescription());
            return result;
        } catch (Exception e) {
            System.err.println("字段查询失败 - " + request.getQueryDescription() + ", 错误: " + e.getMessage());
            throw new RuntimeException("字段查询失败: " + e.getMessage(), e);
        }
    }
        private void validateTableName(String tableName) {
        if (!tableName.matches("^[a-zA-Z_][a-zA-Z0-9_]*$")) {
            throw new IllegalArgumentException("无效的表名: " + tableName);
        }
        if (!tableMapper.tableExists(tableName)) {
            throw new IllegalArgumentException("表不存在: " + tableName);
        }
    }
}
