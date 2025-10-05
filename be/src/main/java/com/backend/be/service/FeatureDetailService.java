package com.backend.be.service;

import com.backend.be.model.FeatureDetailRequest;
import com.backend.be.model.FeatureDetailResponse;

/**
 * 要素详情服务接口
 * 提供空间要素详细信息的查询服务
 */
public interface FeatureDetailService {
    
    /**
     * 获取要素详情
     * @param request 要素详情查询请求
     * @return 要素详情响应
     */
    FeatureDetailResponse getFeatureDetail(FeatureDetailRequest request);
    
    /**
     * 根据表名和要素ID获取要素详情
     * @param tableName 表名
     * @param featureId 要素ID
     * @return 要素详情响应
     */
    FeatureDetailResponse getFeatureDetail(String tableName, String featureId);
    
    /**
     * 检查表是否存在
     * @param tableName 表名
     * @return true 如果表存在
     */
    boolean tableExists(String tableName);
    
    /**
     * 检查要素是否存在
     * @param tableName 表名
     * @param featureId 要素ID
     * @return true 如果要素存在
     */
    boolean featureExists(String tableName, String featureId);
}
