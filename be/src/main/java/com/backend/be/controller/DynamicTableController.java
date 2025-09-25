package com.backend.be.controller;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.backend.be.service.impl.DynamicTableServiceImpl;


@RestController
@RequestMapping("/postgis/WGP_db")
public class DynamicTableController {

    @Autowired
    private DynamicTableServiceImpl tableService;

    /**
     * 获取所有表名
     */
    @GetMapping("/tables")
    public List<String> getAllTableNames() {
        return tableService.getAllTableNames();
    }

    /**
     * 获取表数据
     */
    @GetMapping("/tables/{tableName}/data")
    public List<Map<String, Object>> getTableData(@PathVariable String tableName) {
        return tableService.getTableData(tableName);
    }

    /**
     * 获取表结构
     */
    @GetMapping("/tables/{tableName}/schema")
    public List<Map<String, Object>> getTableSchema(@PathVariable String tableName) {
        return tableService.getTableSchema(tableName);
    }

    @GetMapping("/tables/SpatialTables")
    public List<String> getSpatialTables() {
        return tableService.getSpatialTables();
    }
    @GetMapping("/tables/SpatialTables/{tableName}/geojson")
    public String getSpatialTableGeojson(@PathVariable String tableName) {
        return tableService.getSpatialTableGeojson(tableName);
    }
    @GetMapping("/tables/SpatialTables/{tableName}/querybyname/{name}")
    public String querybyname(@RequestParam String param) {
        return new String();
    }
    


}
