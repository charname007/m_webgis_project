package com.backend.be.model;

import lombok.Data;

import java.util.List;

/**
 * 路线规划响应模型
 * 包含多条路径规划方案，每条路径都是一个GeoJSON FeatureCollection
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class RouteResponse {
    
    /**
     * 路径规划方案总数
     * 表示返回的路径数量
     */
    private Integer count;
    
    /**
     * 路径列表
     * 包含多条路径规划方案
     * 每个路径都是一个RoutePath对象
     */
    private List<RoutePath> paths;
    
    /**
     * 请求状态码
     * 1：成功
     * 0：失败
     */
    private Integer status;
    
    /**
     * 状态信息
     * 成功返回"ok"，失败返回错误原因
     */
    private String info;
    
    /**
     * 信息码
     * 10000代表正确，详情参阅高德地图API状态表
     */
    private String infocode;
}