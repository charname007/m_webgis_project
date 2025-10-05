package com.backend.be.controller;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.backend.be.model.SpatialTableRequest;
import com.backend.be.service.impl.DynamicTableServiceImpl;


@RestController
@RequestMapping("/postgis/WGP_db/dynamic-tables")
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
    // @GetMapping("/tables/SpatialTables/{tableName}/querybyname/{name}")
    // public String querybyname(@RequestParam String param) {
    //     return new String();
    // }
    @PostMapping("/tables/SpatialTables/geojson")
    public String getSpatialTablesGeojson(@RequestBody SpatialTableRequest request) {
        return tableService.getSpatialTablesGeojson(request);
    }

    /**
     * 根据坐标范围查询空间表要素并返回 GeoJSON
     * @param tableName 空间表名
     * @param request 坐标范围请求参数
     * @return GeoJSON 格式的要素集合
     */
    @PostMapping("/tables/SpatialTables/{tableName}/geojson/extent")
    public String getSpatialTableGeojsonByExtent(
        @PathVariable String tableName,
        @RequestBody com.backend.be.model.SpatialExtentRequest request) {
        return tableService.getSpatialTableGeojsonByExtent(tableName, request);
    }

    /**
     * 根据字段条件查询空间表要素并返回 GeoJSON
     * @param request 字段查询请求参数
     * @return GeoJSON 格式的要素集合
     */
    @PostMapping("/tables/SpatialTables/geojson/fields")
    public String getSpatialTableGeojsonByFields(
        @RequestBody com.backend.be.model.FieldQueryRequest request) {
        return tableService.getSpatialTableGeojsonByFields(request);
    }

}
