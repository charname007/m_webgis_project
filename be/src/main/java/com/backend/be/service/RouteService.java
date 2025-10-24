package com.backend.be.service;

import com.backend.be.model.RouteRequest;
import com.backend.be.model.RouteResponse;
import com.backend.be.model.WalkingRouteResponse;
import com.backend.be.model.BicyclingRouteResponse;

/**
 * 路线规划服务接口
 * 定义驾车路线规划相关的业务方法
 * 
 * @author Claude
 * @create 2025-10-24
 */
public interface RouteService {
    
    /**
     * 获取驾车路线规划
     * 调用高德地图驾车路线规划API，返回多条路径方案
     * 
     * @param request 路线规划请求参数
     * @return 路线规划响应，包含多条路径的GeoJSON数据
     */
    RouteResponse getDrivingRoute(RouteRequest request);
    
    /**
    * 获取驾车路线规划（带异常处理）
    *
    * @param request 路线规划请求参数
    * @return 路线规划响应，包含多条路径的GeoJSON数据
    * @throws Exception 路线规划过程中的异常
    */
    RouteResponse getDrivingRouteWithException(RouteRequest request) throws Exception;
    
    /**
     * 获取步行路线规划
     * 调用高德地图步行路线规划API，返回步行路径方案
     * 
     * @param request 路线规划请求参数
     * @return 步行路线规划响应，包含步行路径的详细信息
     */
    WalkingRouteResponse getWalkingRoute(RouteRequest request);
    
    /**
     * 获取步行路线规划（带异常处理）
     * 
     * @param request 路线规划请求参数
     * @return 步行路线规划响应，包含步行路径的详细信息
     * @throws Exception 路线规划过程中的异常
     */
    WalkingRouteResponse getWalkingRouteWithException(RouteRequest request) throws Exception;
    
    /**
     * 获取骑行路线规划
     * 调用高德地图骑行路线规划API，返回骑行路径方案
     * 
     * @param request 路线规划请求参数
     * @return 骑行路线规划响应，包含骑行路径的详细信息
     */
    BicyclingRouteResponse getBicyclingRoute(RouteRequest request);
    
    /**
     * 获取骑行路线规划（带异常处理）
     * 
     * @param request 路线规划请求参数
     * @return 骑行路线规划响应，包含骑行路径的详细信息
     * @throws Exception 路线规划过程中的异常
     */
    BicyclingRouteResponse getBicyclingRouteWithException(RouteRequest request) throws Exception;
}