package com.backend.be.service;

/**
 * 景区服务接口
 * 提供景区相关的查询功能
 */
public interface ASightService {
    
    /**
     * 查询指定范围内的景区要素并返回 GeoJSON
     * @param request 景区查询请求
     * @return GeoJSON 格式的景区要素集合
     */
    String getSightGeojsonByExtentAndLevel(com.backend.be.model.SightQueryRequest request);
}
