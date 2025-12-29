package com.backend.be.service.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.backend.be.model.RouteFeature;
import com.backend.be.model.RoutePath;
import com.backend.be.model.RouteRequest;
import com.backend.be.model.RouteResponse;
import com.backend.be.service.RouteService;
import com.backend.be.util.CoordinateConverter;
import com.backend.be.util.GeoJsonUtil;

import lombok.extern.slf4j.Slf4j;

/**
 * 路线规划服务实现类
 * 实现驾车路线规划业务逻辑，包括坐标转换、API调用和结果解析
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Slf4j
@Service
public class RouteServiceImpl implements RouteService {

    /**
     * 高德地图API密钥
     */
    @Value("${amap.api.key:}")
    private String apiKey;

    /**
     * 高德地图API基础URL
     */
    @Value("${amap.api.base-url:https://restapi.amap.com}")
    private String baseUrl;

    /**
     * HTTP客户端
     */
    private final RestTemplate restTemplate;

    public RouteServiceImpl() {
        this.restTemplate = new RestTemplate();
    }

    @Override
    public RouteResponse getDrivingRoute(RouteRequest request) {
        try {
            // 验证请求参数
            if (!validateRouteRequest(request)) {
                log.error("路线规划请求参数验证失败");
                return createErrorResponse("请求参数不完整或格式错误");
            }
            return getDrivingRouteWithException(request);
        } catch (Exception e) {
            log.error("路线规划失败: {}", e.getMessage(), e);
            return createErrorResponse("路线规划失败: " + e.getMessage());
        }
    }

    @Override
    public RouteResponse getDrivingRouteWithException(RouteRequest request) throws Exception {
        log.info("开始路线规划: {} -> {}", request.getOrigin(), request.getDestination());

        // 1. 坐标转换：WGS84 -> GCJ02
        double[] originGcj02 = CoordinateConverter.wgs84ToGcj02(
                Double.parseDouble(request.getOrigin().split(",")[0]),
                Double.parseDouble(request.getOrigin().split(",")[1])
        );
        double[] destinationGcj02 = CoordinateConverter.wgs84ToGcj02(
                Double.parseDouble(request.getDestination().split(",")[0]),
                Double.parseDouble(request.getDestination().split(",")[1])
        );

        // 2. 构建API请求参数
        Map<String, Object> params = buildApiParams(request, originGcj02, destinationGcj02);

        // 3. 调用高德地图API
        String apiUrl = buildApiUrl(params);
        log.info("调用高德地图API: {}", apiUrl);

        ResponseEntity<Map> response = restTemplate.getForEntity(apiUrl, Map.class);
        Map<String, Object> apiResponse = response.getBody();

        // 4. 验证并解析API响应
        if (!validateApiResponse(apiResponse)) {
            log.error("API响应格式验证失败");
            return createErrorResponse("API响应格式不正确");
        }

        // 调试：打印API响应结构
        log.debug("API响应状态: {}", apiResponse.get("status"));
        log.debug("API响应信息: {}", apiResponse.get("info"));
        if (apiResponse.containsKey("route")) {
            Map<String, Object> route = (Map<String, Object>) apiResponse.get("route");
            log.debug("route字段: {}", route.keySet());
            if (route.containsKey("paths")) {
                List<Map<String, Object>> paths = (List<Map<String, Object>>) route.get("paths");
                log.debug("找到 {} 条路径", paths.size());
                for (int pathIndex = 0; pathIndex < paths.size(); pathIndex++) {
                    Map<String, Object> path = paths.get(pathIndex);
                    log.debug("路径 {} 字段: {}", pathIndex, path.keySet());
                    if (path.containsKey("steps")) {
                        List<Map<String, Object>> steps = (List<Map<String, Object>>) path.get("steps");
                        log.debug("路径 {} 有 {} 个分段", pathIndex, steps.size());
                    }
                }
            }
        }

        return parseApiResponse(apiResponse);
    }

    /**
     * 构建API请求参数
     */
    private Map<String, Object> buildApiParams(RouteRequest request, double[] originGcj02, double[] destinationGcj02) {
        Map<String, Object> params = new HashMap<>();
        
        // 必需参数
        params.put("key", apiKey);
        params.put("origin", originGcj02[0] + "," + originGcj02[1]);
        params.put("destination", destinationGcj02[0] + "," + destinationGcj02[1]);
        params.put("strategy", request.getStrategy());
        
        // 可选参数
        if (request.getWaypoints() != null && !request.getWaypoints().isEmpty()) {
            params.put("waypoints", request.getWaypoints());
        }
        if (request.getAvoidpolygons() != null && !request.getAvoidpolygons().isEmpty()) {
            params.put("avoidpolygons", request.getAvoidpolygons());
        }
        if (request.getAvoidroad() != null && !request.getAvoidroad().isEmpty()) {
            params.put("avoidroad", request.getAvoidroad());
        }
        if (request.getPlate() != null && !request.getPlate().isEmpty()) {
            params.put("plate", request.getPlate());
        }
        if (request.getCartype() != null) {
            params.put("cartype", request.getCartype());
        }
        if (request.getFerry() != null) {
            params.put("ferry", request.getFerry());
        }
        
        // 返回完整字段
        params.put("show_fields", "cost,tmcs,navi,polyline");
        params.put("output", "JSON");
        
        return params;
    }

    /**
     * 构建API URL
     */
    private String buildApiUrl(Map<String, Object> params) {
        StringBuilder urlBuilder = new StringBuilder(baseUrl);
        urlBuilder.append("/v5/direction/driving?");

        for (Map.Entry<String, Object> entry : params.entrySet()) {
            urlBuilder.append(entry.getKey())
                    .append("=")
                    .append(entry.getValue())
                    .append("&");
        }

        // 移除最后一个"&"
        return urlBuilder.substring(0, urlBuilder.length() - 1);
    }

    /**
     * 解析API响应
     */
    @SuppressWarnings("unchecked")
    private RouteResponse parseApiResponse(Map<String, Object> apiResponse) {
        RouteResponse response = new RouteResponse();

        // 设置基础状态信息
        response.setStatus(parseIntegerSafely(apiResponse.get("status")));
        response.setInfo(getStringSafely(apiResponse.get("info")));
        response.setInfocode(getStringSafely(apiResponse.get("infocode")));

        if (response.getStatus() != 1) {
            log.error("高德地图API调用失败: {}", response.getInfo());
            return response;
        }

        // 安全解析路径数据
        Map<String, Object> routeData = null;
        try {
            routeData = (Map<String, Object>) apiResponse.get("route");
            if (routeData == null) {
                log.error("API响应中缺少route字段");
                return createErrorResponse("API响应格式错误：缺少route字段");
            }
        } catch (ClassCastException e) {
            log.error("route字段类型错误: {}", e.getMessage());
            return createErrorResponse("API响应格式错误：route字段类型不正确");
        }

        List<Map<String, Object>> paths = null;
        try {
            paths = (List<Map<String, Object>>) routeData.get("paths");
            if (paths == null || paths.isEmpty()) {
                log.warn("API响应中paths字段为空");
                response.setCount(0);
                response.setPaths(new ArrayList<>());
                return response;
            }
        } catch (ClassCastException e) {
            log.error("paths字段类型错误: {}", e.getMessage());
            return createErrorResponse("API响应格式错误：paths字段类型不正确");
        }

        response.setCount(paths.size());
        response.setPaths(parsePaths(paths));

        log.info("路线规划成功，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 解析多条路径
     */
    @SuppressWarnings("unchecked")
    private List<RoutePath> parsePaths(List<Map<String, Object>> paths) {
        List<RoutePath> routePaths = new ArrayList<>();

        for (int i = 0; i < paths.size(); i++) {
            Map<String, Object> pathData = paths.get(i);
            RoutePath routePath = new RoutePath();

            // 设置路径属性
            RoutePath.PathProperties properties = new RoutePath.PathProperties();
            properties.setPathIndex(i);

            // 安全设置距离和时长（处理字符串和数字类型）
            properties.setTotalDistance(parseDoubleSafely(pathData.get("distance")));
            properties.setTotalDuration(parseDoubleSafely(pathData.get("duration")));

            // 安全设置限制信息
            Object restrictionObj = pathData.get("restriction");
            if (restrictionObj instanceof Boolean) {
                properties.setRestriction((Boolean) restrictionObj);
            } else if (restrictionObj instanceof String) {
                properties.setRestriction(Boolean.parseBoolean((String) restrictionObj));
            } else {
                properties.setRestriction(false); // 默认值
            }

            // 解析费用信息
            Map<String, Object> cost = null;
            try {
                cost = (Map<String, Object>) pathData.get("cost");
            } catch (ClassCastException e) {
                log.warn("路径 {} 的cost字段类型错误: {}", i, e.getMessage());
                cost = null;
            }

            if (cost != null) {
                properties.setTotalTolls(parseDoubleSafely(cost.get("tolls")));
                properties.setTollDistance(parseDoubleSafely(cost.get("toll_distance")));
                properties.setTollRoad((String) cost.get("toll_road"));
                properties.setTaxiFee(parseDoubleSafely(cost.get("taxi_fee")));
                properties.setTrafficLights(parseIntegerSafely(cost.get("traffic_lights")));
            }

            routePath.setProperties(properties);

            // 安全解析分段信息
            List<Map<String, Object>> steps = null;
            try {
                steps = (List<Map<String, Object>>) pathData.get("steps");
            } catch (ClassCastException e) {
                log.warn("路径 {} 的steps字段类型错误: {}", i, e.getMessage());
                steps = new ArrayList<>();
            }

            routePath.setFeatures(parseSteps(steps));

            routePaths.add(routePath);
        }

        return routePaths;
    }

    /**
     * 解析路线分段
     */
    @SuppressWarnings("unchecked")
    private List<RouteFeature> parseSteps(List<Map<String, Object>> steps) {
        List<RouteFeature> features = new ArrayList<>();

        if (steps == null || steps.isEmpty()) {
            log.warn("steps列表为空");
            return features;
        }

        for (int i = 0; i < steps.size(); i++) {
            Map<String, Object> stepData = steps.get(i);

            // 安全解析坐标点和费用信息
            String polyline = null;
            Double tolls = null;
            Double duration = null;
            Double tollDistance = null;
            String tollRoad = null;
            Double taxiFee = null;
            Integer trafficLights = null;
            Map<String, Object> cost = null;
            
            try {
                // 获取cost对象
                cost = (Map<String, Object>) stepData.get("cost");
                
                // 调试日志：打印cost对象结构
                if (cost != null) {
                    log.debug("分段 {} cost对象字段: {}", i, cost.keySet());
                    


                    // 驾车API：优先从stepData.tmcs中获取tmc_polyline
                    // List<Map<String, Object>> tmcs = (List<Map<String, Object>>) stepData.get("tmcs");
                    // if (tmcs != null && !tmcs.isEmpty()) {
                    //     log.debug("分段 {} 找到 {} 个tmc条目", i, tmcs.size());
                    //     for (int tmcIndex = 0; tmcIndex < tmcs.size(); tmcIndex++) {
                    //         Map<String, Object> tmc = tmcs.get(tmcIndex);
                    //         String tmcPolyline = (String) tmc.get("tmc_polyline");
                    //         log.debug("分段 {} tmc[{}] 字段: {}, tmc_polyline: {}", i, tmcIndex, tmc.keySet(), tmcPolyline);
                    //         if (tmcPolyline != null && !tmcPolyline.trim().isEmpty()) {
                    //             polyline = tmcPolyline;
                    //             log.debug("分段 {} 成功获取tmc_polyline: {} 个坐标点", i, tmcPolyline.split(";").length);
                    //             break;
                    //         }
                    //     }
                    // } else {
                    //     log.debug("分段 {} tmcs为空或不存在", i);
                    // }


                } else {
                    log.debug("分段 {} cost对象为空", i);
                }
                
                String Polyline = (String) stepData.get("polyline");

                // 如果驾车API的tmc_polyline为空，则尝试步行/骑行API的polyline字段
                if (polyline == null || polyline.trim().isEmpty()) {
                    polyline = (String) stepData.get("polyline");
                    log.debug("分段 {} 尝试直接获取polyline字段: {}", i, polyline);
                }
            } catch (ClassCastException e) {
                log.warn("分段 {} 的polyline字段类型错误: {}", i, e.getMessage());
                continue; // 跳过此分段，继续处理下一个
            }

            if (polyline == null || polyline.trim().isEmpty()) {
                log.warn("分段 {} 的polyline字段为空，跳过此分段", i);
                // 调试：打印stepData的所有字段
                log.debug("分段 {} stepData字段: {}", i, stepData.keySet());
                continue;
            }

            double[][] coordinates = GeoJsonUtil.parsePolyline(polyline);

            // 坐标转换：GCJ02 -> WGS84
            double[][] wgs84Coordinates = CoordinateConverter.batchGcj02ToWgs84(coordinates);

            // 从cost对象中提取费用信息（cost已经在前面获取）
            if (cost != null) {
                tolls = parseDoubleSafely(cost.get("tolls"));
                duration = parseDoubleSafely(cost.get("duration"));
                tollDistance = parseDoubleSafely(cost.get("toll_distance"));
                tollRoad = getStringSafely(cost.get("toll_road"));
                taxiFee = parseDoubleSafely(cost.get("taxi_fee"));
                trafficLights = parseIntegerSafely(cost.get("traffic_lights"));
            }

            // 安全解析路况信息
            String tmcStatus = null;
            List<Map<String, Object>> tmcs = null;
            try {
                tmcs = (List<Map<String, Object>>) stepData.get("tmcs");
            } catch (ClassCastException e) {
                log.warn("分段 {} 的tmcs字段类型错误: {}", i, e.getMessage());
                tmcs = null;
            }

            if (tmcs != null && !tmcs.isEmpty()) {
                try {
                    tmcStatus = (String) tmcs.get(0).get("tmc_status");
                } catch (ClassCastException e) {
                    log.warn("分段 {} 的tmc_status字段类型错误: {}", i, e.getMessage());
                }
            }

            // 安全解析导航信息
            String action = null;
            String assistantAction = null;
            Map<String, Object> navi = null;
            try {
                navi = (Map<String, Object>) stepData.get("navi");
            } catch (ClassCastException e) {
                log.warn("分段 {} 的navi字段类型错误: {}", i, e.getMessage());
                navi = null;
            }

            if (navi != null) {
                action = (String) navi.get("action");
                assistantAction = (String) navi.get("assistant_action");
            }

            // 安全获取其他字段
            String instruction = getStringSafely(stepData.get("instruction"));
            String orientation = getStringSafely(stepData.get("orientation"));
            String roadName = getStringSafely(stepData.get("road_name"));
            Double stepDistance = parseDoubleSafely(stepData.get("step_distance"));
            // 优先使用cost中的duration，如果没有则使用step级别的duration
            if (duration == null) {
                duration = parseDoubleSafely(stepData.get("duration"));
            }

            // 创建分段Feature
            RouteFeature feature = GeoJsonUtil.createFullRouteFeature(
                    wgs84Coordinates,
                    instruction,
                    orientation,
                    roadName,
                    stepDistance,
                    duration,
                    tolls,
                    tmcStatus,
                    action,
                    assistantAction,
                    i
            );

            features.add(feature);
        }

        return features;
    }

    /**
     * 创建错误响应
     */
    private RouteResponse createErrorResponse(String errorMessage) {
        RouteResponse response = new RouteResponse();
        response.setStatus(0);
        response.setInfo(errorMessage);
        response.setInfocode("50000");
        response.setCount(0);
        response.setPaths(new ArrayList<>());
        return response;
    }

    @Override
    public RouteResponse getWalkingRoute(RouteRequest request) {
        try {
            // 验证请求参数
            if (!validateRouteRequest(request)) {
                log.error("步行路线规划请求参数验证失败");
                return createErrorResponse("请求参数不完整或格式错误");
            }
            return getWalkingRouteWithException(request);
        } catch (Exception e) {
            log.error("步行路线规划失败: {}", e.getMessage(), e);
            return createErrorResponse("步行路线规划失败: " + e.getMessage());
        }
    }

    @Override
    public RouteResponse getWalkingRouteWithException(RouteRequest request) throws Exception {
        log.info("开始步行路线规划: {} -> {}", request.getOrigin(), request.getDestination());

        // 1. 坐标转换：WGS84 -> GCJ02
        double[] originGcj02 = CoordinateConverter.wgs84ToGcj02(
                Double.parseDouble(request.getOrigin().split(",")[0]),
                Double.parseDouble(request.getOrigin().split(",")[1])
        );
        double[] destinationGcj02 = CoordinateConverter.wgs84ToGcj02(
                Double.parseDouble(request.getDestination().split(",")[0]),
                Double.parseDouble(request.getDestination().split(",")[1])
        );

        // 2. 构建步行API请求参数
        Map<String, Object> params = buildWalkingApiParams(request, originGcj02, destinationGcj02);

        // 3. 调用高德地图步行API
        String apiUrl = buildWalkingApiUrl(params);
        log.info("调用高德地图步行API: {}", apiUrl);

        ResponseEntity<Map> response = restTemplate.getForEntity(apiUrl, Map.class);
        Map<String, Object> apiResponse = response.getBody();

        // 4. 验证并解析步行API响应
        if (!validateApiResponse(apiResponse)) {
            log.error("步行API响应格式验证失败");
            return createErrorResponse("API响应格式不正确");
        }

        return parseWalkingApiResponse(apiResponse);
    }

    /**
     * 构建步行API请求参数
     */
    private Map<String, Object> buildWalkingApiParams(RouteRequest request, double[] originGcj02, double[] destinationGcj02) {
        Map<String, Object> params = new HashMap<>();
        
        // 必需参数
        params.put("key", apiKey);
        params.put("origin", originGcj02[0] + "," + originGcj02[1]);
        params.put("destination", destinationGcj02[0] + "," + destinationGcj02[1]);
        
        // 可选参数
        if (request.getOriginId() != null && !request.getOriginId().isEmpty()) {
            params.put("origin_id", request.getOriginId());
        }
        if (request.getDestinationId() != null && !request.getDestinationId().isEmpty()) {
            params.put("destination_id", request.getDestinationId());
        }
        if (request.getSig() != null && !request.getSig().isEmpty()) {
            params.put("sig", request.getSig());
        }
        if (request.getOutput() != null && !request.getOutput().isEmpty()) {
            params.put("output", request.getOutput());
        }
        if (request.getCallback() != null && !request.getCallback().isEmpty()) {
            params.put("callback", request.getCallback());
        }
        
        return params;
    }

    /**
     * 构建步行API URL
     */
    private String buildWalkingApiUrl(Map<String, Object> params) {
        StringBuilder urlBuilder = new StringBuilder(baseUrl);
        urlBuilder.append("/v3/direction/walking?");

        for (Map.Entry<String, Object> entry : params.entrySet()) {
            urlBuilder.append(entry.getKey())
                    .append("=")
                    .append(entry.getValue())
                    .append("&");
        }

        // 移除最后一个"&"
        return urlBuilder.substring(0, urlBuilder.length() - 1);
    }

    /**
     * 解析步行API响应
     */
    @SuppressWarnings("unchecked")
    private RouteResponse parseWalkingApiResponse(Map<String, Object> apiResponse) {
        RouteResponse response = new RouteResponse();

        // 设置基础状态信息
        response.setStatus(parseIntegerSafely(apiResponse.get("status")));
        response.setInfo(getStringSafely(apiResponse.get("info")));
        response.setInfocode(getStringSafely(apiResponse.get("infocode")));

        if (response.getStatus() != 1) {
            log.error("高德地图步行API调用失败: {}", response.getInfo());
            return response;
        }

        // 安全解析路径数据
        Map<String, Object> routeData = null;
        try {
            routeData = (Map<String, Object>) apiResponse.get("route");
            if (routeData == null) {
                log.error("步行API响应中缺少route字段");
                return createErrorResponse("API响应格式错误：缺少route字段");
            }
        } catch (ClassCastException e) {
            log.error("步行API route字段类型错误: {}", e.getMessage());
            return createErrorResponse("API响应格式错误：route字段类型不正确");
        }

        List<Map<String, Object>> paths = null;
        try {
            paths = (List<Map<String, Object>>) routeData.get("paths");
            if (paths == null || paths.isEmpty()) {
                log.warn("步行API响应中paths字段为空");
                response.setCount(0);
                response.setPaths(new ArrayList<>());
                return response;
            }
        } catch (ClassCastException e) {
            log.error("步行API paths字段类型错误: {}", e.getMessage());
            return createErrorResponse("API响应格式错误：paths字段类型不正确");
        }

        response.setCount(paths.size());
        response.setPaths(parseWalkingPaths(paths));

        log.info("步行路线规划成功，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 解析多条步行路径
     */
    @SuppressWarnings("unchecked")
    private List<RoutePath> parseWalkingPaths(List<Map<String, Object>> paths) {
        List<RoutePath> routePaths = new ArrayList<>();

        for (int i = 0; i < paths.size(); i++) {
            Map<String, Object> pathData = paths.get(i);
            RoutePath routePath = new RoutePath();

            // 设置路径属性
            RoutePath.PathProperties properties = new RoutePath.PathProperties();
            properties.setPathIndex(i);
            properties.setTotalDistance(parseDoubleSafely(pathData.get("distance")));
            properties.setTotalDuration(parseDoubleSafely(pathData.get("duration")));
            properties.setRestriction(false); // 步行路线没有限制
            
            routePath.setProperties(properties);

            // 安全解析分段信息
            List<Map<String, Object>> steps = null;
            try {
                steps = (List<Map<String, Object>>) pathData.get("steps");
            } catch (ClassCastException e) {
                log.warn("步行路径steps字段类型错误: {}", e.getMessage());
                steps = new ArrayList<>();
            }

            routePath.setFeatures(parseWalkingSteps(steps));

            routePaths.add(routePath);
        }

        return routePaths;
    }

    /**
     * 解析步行分段
     */
    @SuppressWarnings("unchecked")
    private List<RouteFeature> parseWalkingSteps(List<Map<String, Object>> steps) {
        List<RouteFeature> features = new ArrayList<>();

        if (steps == null || steps.isEmpty()) {
            log.warn("步行steps列表为空");
            return features;
        }

        for (int i = 0; i < steps.size(); i++) {
            Map<String, Object> stepData = steps.get(i);

            // 安全获取polyline字段
            String polyline = getStringSafely(stepData.get("polyline"));
            if (polyline == null || polyline.trim().isEmpty()) {
                log.warn("步行分段 {} 的polyline字段为空，跳过此分段", i);
                continue;
            }

            // 解析坐标点
            double[][] coordinates = GeoJsonUtil.parsePolyline(polyline);

            // 坐标转换：GCJ02 -> WGS84
            double[][] wgs84Coordinates = CoordinateConverter.batchGcj02ToWgs84(coordinates);

            // 安全获取其他字段
            String instruction = getStringSafely(stepData.get("instruction"));
            String orientation = getStringSafely(stepData.get("orientation"));
            String roadName = getStringSafely(stepData.get("road"));
            Double stepDistance = parseDoubleSafely(stepData.get("distance"));
            Double duration = parseDoubleSafely(stepData.get("duration"));
            String action = getStringSafely(stepData.get("action"));
            String assistantAction = getStringSafely(stepData.get("assistant_action"));

            // 创建分段Feature
            RouteFeature feature = GeoJsonUtil.createFullRouteFeature(
                    wgs84Coordinates,
                    instruction,
                    orientation,
                    roadName,
                    stepDistance,
                    duration,
                    0.0, // 步行没有费用
                    null, // 步行没有路况信息
                    action,
                    assistantAction,
                    i
            );

            features.add(feature);
        }

        return features;
    }

    @Override
    public RouteResponse getBicyclingRoute(RouteRequest request) {
        try {
            // 验证请求参数
            if (!validateRouteRequest(request)) {
                log.error("骑行路线规划请求参数验证失败");
                return createErrorResponse("请求参数不完整或格式错误");
            }
            return getBicyclingRouteWithException(request);
        } catch (Exception e) {
            log.error("骑行路线规划失败: {}", e.getMessage(), e);
            return createErrorResponse("骑行路线规划失败: " + e.getMessage());
        }
    }

    @Override
    public RouteResponse getBicyclingRouteWithException(RouteRequest request) throws Exception {
        log.info("开始骑行路线规划: {} -> {}", request.getOrigin(), request.getDestination());

        // 1. 坐标转换：WGS84 -> GCJ02
        double[] originGcj02 = CoordinateConverter.wgs84ToGcj02(
                Double.parseDouble(request.getOrigin().split(",")[0]),
                Double.parseDouble(request.getOrigin().split(",")[1])
        );
        double[] destinationGcj02 = CoordinateConverter.wgs84ToGcj02(
                Double.parseDouble(request.getDestination().split(",")[0]),
                Double.parseDouble(request.getDestination().split(",")[1])
        );

        // 2. 构建骑行API请求参数
        Map<String, Object> params = buildBicyclingApiParams(request, originGcj02, destinationGcj02);

        // 3. 调用高德地图骑行API
        String apiUrl = buildBicyclingApiUrl(params);
        log.info("调用高德地图骑行API: {}", apiUrl);

        ResponseEntity<Map> response = restTemplate.getForEntity(apiUrl, Map.class);
        Map<String, Object> apiResponse = response.getBody();

        // 4. 解析骑行API响应
        return parseBicyclingApiResponse(apiResponse);
    }

    /**
     * 构建骑行API请求参数
     */
    private Map<String, Object> buildBicyclingApiParams(RouteRequest request, double[] originGcj02, double[] destinationGcj02) {
        Map<String, Object> params = new HashMap<>();
        
        // 必需参数
        params.put("key", apiKey);
        params.put("origin", originGcj02[0] + "," + originGcj02[1]);
        params.put("destination", destinationGcj02[0] + "," + destinationGcj02[1]);
        
        // 骑行API特有参数（根据API文档，目前只有必需参数）
        // 可选参数可以在这里添加，如果API支持的话
        
        return params;
    }

    /**
     * 构建骑行API URL
     */
    private String buildBicyclingApiUrl(Map<String, Object> params) {
        StringBuilder urlBuilder = new StringBuilder(baseUrl);
        urlBuilder.append("/v4/direction/bicycling?");

        for (Map.Entry<String, Object> entry : params.entrySet()) {
            urlBuilder.append(entry.getKey())
                    .append("=")
                    .append(entry.getValue())
                    .append("&");
        }

        // 移除最后一个"&"
        return urlBuilder.substring(0, urlBuilder.length() - 1);
    }

    /**
     * 解析骑行API响应
     */
    @SuppressWarnings("unchecked")
    private RouteResponse parseBicyclingApiResponse(Map<String, Object> apiResponse) {
        RouteResponse response = new RouteResponse();

        // 4. 验证API响应基本结构
        if (!validateBicyclingApiResponse(apiResponse)) {
            log.error("骑行API响应格式验证失败");
            response.setStatus(0);
            response.setInfo("API响应格式不正确");
            response.setInfocode("50000");
            return response;
        }

        // 骑行API使用不同的状态码字段
        Integer errcode = parseIntegerSafely(apiResponse.get("errcode"));
        String errmsg = getStringSafely(apiResponse.get("errmsg"));

        if (errcode != 0) {
            log.error("高德地图骑行API调用失败: {} (errcode: {})", errmsg, errcode);
            response.setStatus(0);
            response.setInfo(errmsg);
            response.setInfocode(String.valueOf(errcode));
            return response;
        }

        // API调用成功
        response.setStatus(1);
        response.setInfo("OK");
        response.setInfocode("10000");

        // 安全解析数据
        Map<String, Object> data = null;
        try {
            data = (Map<String, Object>) apiResponse.get("data");
        } catch (ClassCastException e) {
            log.error("骑行API data字段类型错误: {}", e.getMessage());
            data = null;
        }

        if (data != null) {
            List<Map<String, Object>> paths = null;
            try {
                paths = (List<Map<String, Object>>) data.get("paths");
            } catch (ClassCastException e) {
                log.error("骑行API paths字段类型错误: {}", e.getMessage());
                paths = null;
            }

            response.setCount(paths != null ? paths.size() : 0);
            response.setPaths(parseBicyclingPaths(paths));
        } else {
            response.setCount(0);
            response.setPaths(new ArrayList<>());
        }

        log.info("骑行路线规划成功，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 解析多条骑行路径
     */
    @SuppressWarnings("unchecked")
    private List<RoutePath> parseBicyclingPaths(List<Map<String, Object>> paths) {
        List<RoutePath> routePaths = new ArrayList<>();

        if (paths == null) {
            return routePaths;
        }

        for (int i = 0; i < paths.size(); i++) {
            Map<String, Object> pathData = paths.get(i);
            RoutePath routePath = new RoutePath();

            // 设置路径属性
            RoutePath.PathProperties properties = new RoutePath.PathProperties();
            properties.setPathIndex(i);
            properties.setTotalDistance(parseDoubleSafely(pathData.get("distance")));
            properties.setTotalDuration(parseDoubleSafely(pathData.get("duration")));
            properties.setRestriction(false); // 骑行路线没有限制
            
            routePath.setProperties(properties);

            // 安全解析分段信息
            List<Map<String, Object>> steps = null;
            try {
                steps = (List<Map<String, Object>>) pathData.get("steps");
            } catch (ClassCastException e) {
                log.warn("骑行路径steps字段类型错误: {}", e.getMessage());
                steps = new ArrayList<>();
            }

            routePath.setFeatures(parseBicyclingSteps(steps));

            routePaths.add(routePath);
        }

        return routePaths;
    }

    /**
     * 解析骑行分段
     */
    @SuppressWarnings("unchecked")
    private List<RouteFeature> parseBicyclingSteps(List<Map<String, Object>> steps) {
        List<RouteFeature> features = new ArrayList<>();

        if (steps == null || steps.isEmpty()) {
            log.warn("骑行steps列表为空");
            return features;
        }

        for (int i = 0; i < steps.size(); i++) {
            Map<String, Object> stepData = steps.get(i);

            // 安全获取polyline字段
            String polyline = getStringSafely(stepData.get("polyline"));
            if (polyline == null || polyline.trim().isEmpty()) {
                log.warn("骑行分段 {} 的polyline字段为空，跳过此分段", i);
                continue;
            }

            // 解析坐标点
            double[][] coordinates = GeoJsonUtil.parsePolyline(polyline);

            // 坐标转换：GCJ02 -> WGS84
            double[][] wgs84Coordinates = CoordinateConverter.batchGcj02ToWgs84(coordinates);

            // 安全获取其他字段
            String instruction = getStringSafely(stepData.get("instruction"));
            String orientation = getStringSafely(stepData.get("orientation"));
            String roadName = getStringSafely(stepData.get("road"));
            Double stepDistance = parseDoubleSafely(stepData.get("distance"));
            Double duration = parseDoubleSafely(stepData.get("duration"));
            String action = getStringSafely(stepData.get("action"));
            String assistantAction = getStringSafely(stepData.get("assistant_action"));

            // 创建分段Feature
            RouteFeature feature = GeoJsonUtil.createFullRouteFeature(
                    wgs84Coordinates,
                    instruction,
                    orientation,
                    roadName,
                    stepDistance,
                    duration,
                    0.0, // 骑行没有费用
                    null, // 骑行没有路况信息
                    action,
                    assistantAction,
                    i
            );

            features.add(feature);
        }

        return features;
    }

    /**
     * 安全解析Double值，处理字符串和数字类型
     */
    private Double parseDoubleSafely(Object value) {
        if (value == null) {
            return 0.0;
        }
        if (value instanceof Double) {
            return (Double) value;
        }
        if (value instanceof Integer) {
            return ((Integer) value).doubleValue();
        }
        if (value instanceof String) {
            try {
                return Double.parseDouble((String) value);
            } catch (NumberFormatException e) {
                log.warn("Double解析失败: {}", value);
                return 0.0;
            }
        }
        log.warn("未知的Double类型: {}", value.getClass().getSimpleName());
        return 0.0;
    }

    /**
     * 安全解析Integer值，处理字符串和数字类型
     */
    private Integer parseIntegerSafely(Object value) {
        if (value == null) {
            return 0;
        }
        if (value instanceof Integer) {
            return (Integer) value;
        }
        if (value instanceof Double) {
            return ((Double) value).intValue();
        }
        if (value instanceof String) {
            try {
                return Integer.parseInt((String) value);
            } catch (NumberFormatException e) {
                log.warn("Integer解析失败: {}", value);
                return 0;
            }
        }
        log.warn("未知的Integer类型: {}", value.getClass().getSimpleName());
        return 0;
    }

    /**
     * 安全获取字符串值
     */
    private String getStringSafely(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof String) {
            return (String) value;
        }
        return String.valueOf(value);
    }

    /**
     * 验证API响应基本结构
     */
    private boolean validateApiResponse(Map<String, Object> apiResponse) {
        if (apiResponse == null) {
            log.error("API响应为空");
            return false;
        }

        // 检查必需字段
        if (!apiResponse.containsKey("status")) {
            log.error("API响应缺少status字段");
            return false;
        }

        if (!apiResponse.containsKey("info")) {
            log.error("API响应缺少info字段");
            return false;
        }

        return true;
    }

    /**
     * 验证骑行API响应基本结构
     */
    private boolean validateBicyclingApiResponse(Map<String, Object> apiResponse) {
        if (apiResponse == null) {
            log.error("骑行API响应为空");
            return false;
        }

        // 检查必需字段
        if (!apiResponse.containsKey("errcode")) {
            log.error("骑行API响应缺少errcode字段");
            return false;
        }

        if (!apiResponse.containsKey("errmsg")) {
            log.error("骑行API响应缺少errmsg字段");
            return false;
        }

        return true;
    }

    /**
     * 验证路线规划请求参数
     */
    private boolean validateRouteRequest(RouteRequest request) {
        if (request == null) {
            log.error("路线规划请求为空");
            return false;
        }

        // 验证起点和终点
        if (request.getOrigin() == null || request.getOrigin().trim().isEmpty()) {
            log.error("路线规划请求缺少起点坐标");
            return false;
        }

        if (request.getDestination() == null || request.getDestination().trim().isEmpty()) {
            log.error("路线规划请求缺少终点坐标");
            return false;
        }

        // 验证坐标格式
        if (!isValidCoordinateFormat(request.getOrigin())) {
            log.error("起点坐标格式不正确: {}", request.getOrigin());
            return false;
        }

        if (!isValidCoordinateFormat(request.getDestination())) {
            log.error("终点坐标格式不正确: {}", request.getDestination());
            return false;
        }

        // 验证策略参数
        if (request.getStrategy() == null || request.getStrategy()==0) {
            log.warn("路线规划策略未指定，使用默认策略");
            request.setStrategy(0); // 默认策略
        }

        return true;
    }

    /**
     * 验证坐标格式
     */
    private boolean isValidCoordinateFormat(String coordinate) {
        if (coordinate == null || coordinate.trim().isEmpty()) {
            return false;
        }

        String[] parts = coordinate.split(",");
        if (parts.length != 2) {
            return false;
        }

        try {
            double lng = Double.parseDouble(parts[0].trim());
            double lat = Double.parseDouble(parts[1].trim());

            // 验证经纬度范围
            if (lng < -180 || lng > 180 || lat < -90 || lat > 90) {
                return false;
            }

            return true;
        } catch (NumberFormatException e) {
            return false;
        }
    }
}