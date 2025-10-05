package com.backend.be.mapper;

import org.apache.ibatis.annotations.Mapper;

/**
 * 景区数据访问接口
 * 提供景区相关的数据查询功能
 */
@Mapper
public interface ASightMapper {
    
    /**
     * 查询指定范围内的景区要素并返回 GeoJSON
     * @param request 景区查询请求
     * @return GeoJSON 格式的景区要素集合
     */
    String getSightGeojsonByExtentAndLevel(com.backend.be.model.SightQueryRequest request);
}
