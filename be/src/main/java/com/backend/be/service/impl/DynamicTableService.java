package com.backend.be.service.impl;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.backend.be.mapper.DynamicTableMapper;

@Service
public class DynamicTableService {

    @Autowired
    private DynamicTableMapper tableMapper;

    public List<String> getAllTableNames() {
        return tableMapper.getAllTableNames();
    }

    public List<Map<String, Object>> getTableData(String tableName) {
        validateTableName(tableName);
        return tableMapper.getTableData(tableName);
    }

    public List<Map<String, Object>> getTableSchema(String tableName) {
        validateTableName(tableName);
        return tableMapper.getTableSchema(tableName);
    }

    private void validateTableName(String tableName) {
        if (!tableName.matches("^[a-zA-Z_][a-zA-Z0-9_]*$")) {
            throw new IllegalArgumentException("无效的表名: " + tableName);
        }
        if (!tableMapper.tableExists(tableName)) {
            throw new IllegalArgumentException("表不存在: " + tableName);
        }
    }

    public List<String> getSpatialTables() {
        // TODO Auto-generated method stub
        // throw new UnsupportedOperationException("Unimplemented method 'getSpatialTables'");
        return tableMapper.getSpatialTables();
    }
}
