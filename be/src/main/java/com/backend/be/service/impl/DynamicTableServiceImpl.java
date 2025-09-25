package com.backend.be.service.impl;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.backend.be.service.DynamicTableService;
import com.backend.be.mapper.DynamicTableMapper;

@Service
public class DynamicTableServiceImpl implements DynamicTableService {

    @Autowired
    private DynamicTableMapper tableMapper;

    @Override
    public List<String> getAllTableNames() {
        return tableMapper.getAllTableNames();
    }

    @Override
    public List<Map<String, Object>> getTableData(String tableName) {
        validateTableName(tableName);
        return tableMapper.getTableData(tableName);
    }

    @Override
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
    @Override
    public List<String> getSpatialTables() {
        // TODO Auto-generated method stub
        // throw new UnsupportedOperationException("Unimplemented method 'getSpatialTables'");
        return tableMapper.getSpatialTables();
    }

    public String getSpatialTableGeojson(String tableName) {
        // TODO Auto-generated method stub
        // throw new UnsupportedOperationException("Unimplemented method 'getSpatialTableGeojson'");
        return tableMapper.getSpatialTableGeojson(tableName);
    }
}
