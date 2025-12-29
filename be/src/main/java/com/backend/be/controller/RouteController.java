package com.backend.be.controller;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.backend.be.model.RouteRequest;
import com.backend.be.model.RouteResponse;
import com.backend.be.service.RouteService;

import lombok.extern.slf4j.Slf4j;

/**
 * 路线规划控制器
 * 提供驾车路线规划的RESTful API接口
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Slf4j
@RestController
@RequestMapping("/route")
public class RouteController {

    @Autowired
    private RouteService routeService;

    /**
     * 驾车路线规划接口
     * 根据起点和终点坐标，返回多条驾车路线规划方案
     * 
     * @param request 路线规划请求参数
     * @return 路线规划响应，包含多条路径的GeoJSON数据
     */
    @PostMapping("/driving")
    public RouteResponse getDrivingRoute(@Valid @RequestBody RouteRequest request) {
        log.info("接收到驾车路线规划请求: origin={}, destination={}, strategy={}", 
                request.getOrigin(), request.getDestination(), request.getStrategy());
        
        // 参数验证
        validateRouteRequest(request);
        
        // 调用路线规划服务
        RouteResponse response = routeService.getDrivingRoute(request);
        
        log.info("驾车路线规划完成，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 驾车路线规划接口（GET方式）
     * 支持通过URL参数传递起点和终点坐标
     * 
     * @param origin 起点坐标，格式："经度,纬度"
     * @param destination 终点坐标，格式："经度,纬度"
     * @param strategy 驾车策略，默认32
     * @return 路线规划响应，包含多条路径的GeoJSON数据
     */
    @GetMapping("/driving")
    public RouteResponse getDrivingRouteByGet(
            @RequestParam String origin,
            @RequestParam String destination,
            @RequestParam(required = false, defaultValue = "32") Integer strategy) {
        
        log.info("接收到驾车路线规划GET请求: origin={}, destination={}, strategy={}", 
                origin, destination, strategy);
        
        // 构建请求对象
        RouteRequest request = new RouteRequest();
        request.setOrigin(origin);
        request.setDestination(destination);
        request.setStrategy(strategy);
        
        // 参数验证
        validateRouteRequest(request);
        
        // 调用路线规划服务
        RouteResponse response = routeService.getDrivingRoute(request);
        
        log.info("驾车路线规划完成，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 路线规划请求参数验证
     * 
     * @param request 路线规划请求
     */
    private void validateRouteRequest(RouteRequest request) {
        if (request.getOrigin() == null || request.getOrigin().trim().isEmpty()) {
            throw new IllegalArgumentException("起点坐标不能为空");
        }
        
        if (request.getDestination() == null || request.getDestination().trim().isEmpty()) {
            throw new IllegalArgumentException("终点坐标不能为空");
        }
        
        // 验证坐标格式
        validateCoordinateFormat(request.getOrigin(), "起点");
        validateCoordinateFormat(request.getDestination(), "终点");
        
        // 验证策略参数
        if (request.getStrategy() != null && (request.getStrategy() < 32 || request.getStrategy() > 45)) {
            throw new IllegalArgumentException("驾车策略参数无效，有效范围：32-45");
        }
        
        // 验证车辆类型
        if (request.getCartype() != null && (request.getCartype() < 0 || request.getCartype() > 2)) {
            throw new IllegalArgumentException("车辆类型参数无效，有效值：0-2");
        }
        
        // 验证轮渡参数
        if (request.getFerry() != null && (request.getFerry() < 0 || request.getFerry() > 1)) {
            throw new IllegalArgumentException("轮渡参数无效，有效值：0-1");
        }
    }

    /**
     * 验证坐标格式
     * 
     * @param coordinate 坐标字符串
     * @param fieldName 字段名称
     */
    private void validateCoordinateFormat(String coordinate, String fieldName) {
        String[] parts = coordinate.split(",");
        if (parts.length != 2) {
            throw new IllegalArgumentException(fieldName + "坐标格式错误，应为'经度,纬度'格式");
        }
        
        try {
            double lng = Double.parseDouble(parts[0]);
            double lat = Double.parseDouble(parts[1]);
            
            // 验证经度范围
            if (lng < -180 || lng > 180) {
                throw new IllegalArgumentException(fieldName + "经度范围错误，应在-180到180之间");
            }
            
            // 验证纬度范围
            if (lat < -90 || lat > 90) {
                throw new IllegalArgumentException(fieldName + "纬度范围错误，应在-90到90之间");
            }
            
            // 验证坐标精度 - 符合高德地图API精度要求（小数点后最多6位）
            String lngStr = parts[0];
            String latStr = parts[1];
            if (lngStr.contains(".") && lngStr.split("\\.")[1].length() > 6) {
                throw new IllegalArgumentException(fieldName + "经度小数点后不得超过6位（高德地图API限制）");
            }
            if (latStr.contains(".") && latStr.split("\\.")[1].length() > 6) {
                throw new IllegalArgumentException(fieldName + "纬度小数点后不得超过6位（高德地图API限制）");
            }
            
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(fieldName + "坐标格式错误，应为数字格式");
        }
    }

    /**
     * 异常处理
     *
     * @param e 异常
     * @return 错误响应
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public RouteResponse handleIllegalArgumentException(IllegalArgumentException e) {
        log.warn("参数验证失败: {}", e.getMessage());

        RouteResponse response = new RouteResponse();
        response.setStatus(0);
        response.setInfo(e.getMessage());
        response.setInfocode("40000");
        response.setCount(0);

        return response;
    }

    /**
     /**
     * 步行路线规划接口
     * 根据起点和终点坐标，返回步行路线规划方案
     *
     * @param request 路线规划请求参数
     * @return 路线规划响应，包含步行路径的GeoJSON数据
     */
    @PostMapping("/walking")
    public RouteResponse getWalkingRoute(@Valid @RequestBody RouteRequest request) {
        log.info("接收到步行路线规划请求: origin={}, destination={}",
                request.getOrigin(), request.getDestination());

        // 参数验证
        validateWalkingRouteRequest(request);

        // 调用步行路线规划服务
        RouteResponse response = routeService.getWalkingRoute(request);

        log.info("步行路线规划完成，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 步行路线规划接口（GET方式）
     * 支持通过URL参数传递起点和终点坐标
     *
     * @param origin 起点坐标，格式："经度,纬度"
     * @param destination 终点坐标，格式："经度,纬度"
     * @return 路线规划响应，包含步行路径的GeoJSON数据
     */
    @GetMapping("/walking")
    public RouteResponse getWalkingRouteByGet(
            @RequestParam String origin,
            @RequestParam String destination) {

        log.info("接收到步行路线规划GET请求: origin={}, destination={}",
                origin, destination);

        // 构建请求对象
        RouteRequest request = new RouteRequest();
        request.setOrigin(origin);
        request.setDestination(destination);

        // 参数验证
        validateWalkingRouteRequest(request);

        // 调用步行路线规划服务
        RouteResponse response = routeService.getWalkingRoute(request);

        log.info("步行路线规划完成，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 步行路线规划请求参数验证
     * 
     * @param request 路线规划请求
     */
    private void validateWalkingRouteRequest(RouteRequest request) {
        if (request.getOrigin() == null || request.getOrigin().trim().isEmpty()) {
            throw new IllegalArgumentException("起点坐标不能为空");
        }
        
        if (request.getDestination() == null || request.getDestination().trim().isEmpty()) {
            throw new IllegalArgumentException("终点坐标不能为空");
        }
        
        // 验证坐标格式
        validateCoordinateFormat(request.getOrigin(), "起点");
        validateCoordinateFormat(request.getDestination(), "终点");
        
        // 步行API特有参数验证
        if (request.getOriginId() != null && request.getOriginId().length() > 50) {
            throw new IllegalArgumentException("起点ID长度不能超过50个字符");
        }
        
        if (request.getDestinationId() != null && request.getDestinationId().length() > 50) {
            throw new IllegalArgumentException("终点ID长度不能超过50个字符");
        }
        
        if (request.getSig() != null && request.getSig().length() > 32) {
            throw new IllegalArgumentException("签名参数长度不能超过32个字符");
        }
        
        if (request.getOutput() != null && !request.getOutput().equals("JSON") && !request.getOutput().equals("XML")) {
            throw new IllegalArgumentException("输出格式参数无效，有效值：JSON, XML");
        }
        
        if (request.getCallback() != null && request.getCallback().length() > 100) {
            throw new IllegalArgumentException("回调函数名称长度不能超过100个字符");
        }
    }

    // 步行路线规划异常处理已统一到通用异常处理方法中

    /**
     * 骑行路线规划接口
     * 根据起点和终点坐标，返回骑行路线规划方案
     * 支持500KM以内的骑行路线规划，包含详细的骑行动作和道路类型信息
     * 
     * @param request 路线规划请求参数
     * @return 骑行路线规划响应，包含骑行路径的详细信息
     */
    @PostMapping("/bicycling")
    public RouteResponse getBicyclingRoute(@Valid @RequestBody RouteRequest request) {
        log.info("接收到骑行路线规划请求: origin={}, destination={}", 
                request.getOrigin(), request.getDestination());
        
        // 参数验证
        validateBicyclingRouteRequest(request);
        
        // 调用骑行路线规划服务
        RouteResponse response = routeService.getBicyclingRoute(request);
        
        log.info("骑行路线规划完成，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 骑行路线规划接口（GET方式）
     * 支持通过URL参数传递起点和终点坐标
     * 支持500KM以内的骑行路线规划，包含详细的骑行动作和道路类型信息
     * 
     * @param origin 起点坐标，格式："经度,纬度"
     * @param destination 终点坐标，格式："经度,纬度"
     * @return 骑行路线规划响应，包含骑行路径的详细信息
     */
    @GetMapping("/bicycling")
    public RouteResponse getBicyclingRouteByGet(
            @RequestParam String origin,
            @RequestParam String destination) {
        
        log.info("接收到骑行路线规划GET请求: origin={}, destination={}", 
                origin, destination);
        
        // 构建请求对象
        RouteRequest request = new RouteRequest();
        request.setOrigin(origin);
        request.setDestination(destination);
        
        // 参数验证
        validateBicyclingRouteRequest(request);
        
        // 调用骑行路线规划服务
        RouteResponse response = routeService.getBicyclingRoute(request);
        
        log.info("骑行路线规划完成，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 骑行路线规划请求参数验证
     * 
     * @param request 路线规划请求
     */
    private void validateBicyclingRouteRequest(RouteRequest request) {
        if (request.getOrigin() == null || request.getOrigin().trim().isEmpty()) {
            throw new IllegalArgumentException("起点坐标不能为空");
        }
        
        if (request.getDestination() == null || request.getDestination().trim().isEmpty()) {
            throw new IllegalArgumentException("终点坐标不能为空");
        }
        
        // 验证坐标格式
        validateCoordinateFormat(request.getOrigin(), "起点");
        validateCoordinateFormat(request.getDestination(), "终点");
        
        // 骑行API特有参数验证
        if (request.getOriginId() != null && request.getOriginId().length() > 50) {
            throw new IllegalArgumentException("起点ID长度不能超过50个字符");
        }
        
        if (request.getDestinationId() != null && request.getDestinationId().length() > 50) {
            throw new IllegalArgumentException("终点ID长度不能超过50个字符");
        }
        
        if (request.getSig() != null && request.getSig().length() > 32) {
            throw new IllegalArgumentException("签名参数长度不能超过32个字符");
        }
        
        if (request.getOutput() != null && !request.getOutput().equals("JSON") && !request.getOutput().equals("XML")) {
            throw new IllegalArgumentException("输出格式参数无效，有效值：JSON, XML");
        }
        
        if (request.getCallback() != null && request.getCallback().length() > 100) {
            throw new IllegalArgumentException("回调函数名称长度不能超过100个字符");
        }
    }

    // 骑行路线规划异常处理已统一到通用异常处理方法中

    @ExceptionHandler(Exception.class)
    public RouteResponse handleException(Exception e) {
        log.error("路线规划服务异常: {}", e.getMessage(), e);
        
        RouteResponse response = new RouteResponse();
        response.setStatus(0);
        response.setInfo("服务器内部错误: " + e.getMessage());
        response.setInfocode("50000");
        response.setCount(0);
        
        return response;
    }
}