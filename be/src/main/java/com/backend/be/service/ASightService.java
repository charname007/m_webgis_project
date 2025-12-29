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

    /**
     * 根据名称更新景区信息
     * @param aSight 景区实体对象
     * @return 更新是否成功
     */
    boolean updateByName(com.backend.be.model.ASight aSight);

    /**
     * 插入景区信息
     * @param aSight 景区实体对象
     * @return 插入是否成功
     */
    boolean insert(com.backend.be.model.ASight aSight);

    /**
     * 根据名称更新或插入景区信息（upsert操作）
     * 如果记录存在则更新，不存在则插入
     * @param aSight 景区实体对象
     * @return 操作是否成功
     */
    boolean upsertByName(com.backend.be.model.ASight aSight);

    /**
     * 根据名称删除景区信息
     * @param name 景区名称
     * @return 删除是否成功
     */
    boolean deleteByName(String name);

    /**
     * 根据名称搜索景区并返回 GeoJSON（支持模糊匹配）
     * @param name 景区名称（支持模糊匹配）
     * @return GeoJSON 格式的景区要素集合
     */
    String getSightGeojsonByName(String name);
}
