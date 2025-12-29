package com.backend.be.mapper;

import java.util.Map;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 要素详情数据访问接口
 * 用于查询空间要素的详细信息，包括属性数据和图片链接
 */
@Mapper
public interface FeatureDetailMapper {
    
    /**
     * 检查表是否存在
     * @param tableName 表名
     * @return true 如果表存在
     */
    boolean tableExists(@Param("tableName") String tableName);
    
    /**
     * 检查要素是否存在
     * @param tableName 表名
     * @param featureId 要素ID
     * @return true 如果要素存在
     */
    boolean featureExists(@Param("tableName") String tableName, @Param("featureId") String featureId);
    
    /**
     * 获取要素详情
     * @param tableName 表名
     * @param featureId 要素ID
     * @return 要素属性数据
     */
    Map<String, Object> getFeatureDetail(@Param("tableName") String tableName, @Param("featureId") String featureId);
    
    /**
     * 获取表的主键字段名
     * @param tableName 表名
     * @return 主键字段名
     */
    String getPrimaryKeyColumn(@Param("tableName") String tableName);
    
    /**
     * 获取表的字段信息
     * @param tableName 表名
     * @return 字段信息列表
     */
    java.util.List<Map<String, Object>> getTableColumns(@Param("tableName") String tableName);
}
