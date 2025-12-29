package com.backend.be.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.backend.be.model.FeatureDetailRequest;
import com.backend.be.model.FeatureDetailResponse;
import com.backend.be.service.FeatureDetailService;

/**
 * 要素详情控制器
 * 提供空间要素详细信息的REST API接口
 */
@RestController
@RequestMapping("/postgis/WGP_db")
public class FeatureDetailController {

    @Autowired
    private FeatureDetailService featureDetailService;

    /**
     * 获取要素详情（通过请求体）
     * @param request 要素详情查询请求
     * @return 要素详情响应
     */
    @PostMapping("/tables/{tableName}/features/detail")
    public FeatureDetailResponse getFeatureDetail(
            @PathVariable String tableName,
            @RequestBody FeatureDetailRequest request) {
        
        // 确保路径参数与请求体中的表名一致
        if (!tableName.equals(request.getTableName())) {
            return FeatureDetailResponse.error(tableName, request.getFeatureId(), 
                    "路径参数中的表名与请求体中的表名不一致");
        }
        
        return featureDetailService.getFeatureDetail(request);
    }

    /**
     * 获取要素详情（通过路径参数）
     * @param tableName 表名
     * @param featureId 要素ID
     * @return 要素详情响应
     */
    @GetMapping("/tables/{tableName}/features/{featureId}/detail")
    public FeatureDetailResponse getFeatureDetail(
            @PathVariable String tableName,
            @PathVariable String featureId) {
        
        return featureDetailService.getFeatureDetail(tableName, featureId);
    }

    /**
     * 检查表是否存在
     * @param tableName 表名
     * @return true 如果表存在
     */
    @GetMapping("/tables/{tableName}/exists")
    public boolean tableExists(@PathVariable String tableName) {
        return featureDetailService.tableExists(tableName);
    }

    /**
     * 检查要素是否存在
     * @param tableName 表名
     * @param featureId 要素ID
     * @return true 如果要素存在
     */
    @GetMapping("/tables/{tableName}/features/{featureId}/exists")
    public boolean featureExists(
            @PathVariable String tableName,
            @PathVariable String featureId) {
        
        return featureDetailService.featureExists(tableName, featureId);
    }
}
