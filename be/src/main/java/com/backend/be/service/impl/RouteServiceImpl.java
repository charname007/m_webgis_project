package com.backend.be.service.impl;

import com.backend.be.model.*;
import com.backend.be.service.RouteService;
import com.backend.be.util.CoordinateConverter;
import com.backend.be.util.GeoJsonUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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

        // 4. 解析API响应
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
        params.put("show_fields", "cost,tmcs,navi");
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
        response.setStatus((Integer) apiResponse.get("status"));
        response.setInfo((String) apiResponse.get("info"));
        response.setInfocode(String.valueOf(apiResponse.get("infocode")));
        
        if (response.getStatus() != 1) {
            log.error("高德地图API调用失败: {}", response.getInfo());
            return response;
        }
        
        // 解析路径数据
        Map<String, Object> routeData = (Map<String, Object>) apiResponse.get("route");
        List<Map<String, Object>> paths = (List<Map<String, Object>>) routeData.get("paths");
        
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
            properties.setTotalDistance((Double) pathData.get("distance"));
            properties.setTotalDuration((Double) pathData.get("duration"));
            properties.setRestriction((Boolean) pathData.get("restriction"));
            
            // 解析费用信息
            Map<String, Object> cost = (Map<String, Object>) pathData.get("cost");
            if (cost != null) {
                properties.setTotalTolls((Double) cost.get("tolls"));
                properties.setTollDistance((Double) cost.get("toll_distance"));
                properties.setTollRoad((String) cost.get("toll_road"));
                properties.setTaxiFee((Double) cost.get("taxi_fee"));
                properties.setTrafficLights((Integer) cost.get("traffic_lights"));
            }
            
            routePath.setProperties(properties);
            
            // 解析分段信息
            List<Map<String, Object>> steps = (List<Map<String, Object>>) pathData.get("steps");
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
        
        for (int i = 0; i < steps.size(); i++) {
            Map<String, Object> stepData = steps.get(i);
            
            // 解析坐标点
            String polyline = (String) stepData.get("polyline");
            double[][] coordinates = GeoJsonUtil.parsePolyline(polyline);
            
            // 坐标转换：GCJ02 -> WGS84
            double[][] wgs84Coordinates = CoordinateConverter.batchGcj02ToWgs84(coordinates);
            
            // 解析费用信息
            Double tolls = null;
            Map<String, Object> cost = (Map<String, Object>) stepData.get("cost");
            if (cost != null) {
                tolls = (Double) cost.get("tolls");
            }
            
            // 解析路况信息
            String tmcStatus = null;
            List<Map<String, Object>> tmcs = (List<Map<String, Object>>) stepData.get("tmcs");
            if (tmcs != null && !tmcs.isEmpty()) {
                tmcStatus = (String) tmcs.get(0).get("tmc_status");
            }
            
            // 解析导航信息
            String action = null;
            String assistantAction = null;
            Map<String, Object> navi = (Map<String, Object>) stepData.get("navi");
            if (navi != null) {
                action = (String) navi.get("action");
                assistantAction = (String) navi.get("assistant_action");
            }
            
            // 创建分段Feature
            RouteFeature feature = GeoJsonUtil.createFullRouteFeature(
                    wgs84Coordinates,
                    (String) stepData.get("instruction"),
                    (String) stepData.get("orientation"),
                    (String) stepData.get("road_name"),
                    (Double) stepData.get("step_distance"),
                    (Double) stepData.get("duration"),
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
    public WalkingRouteResponse getWalkingRoute(RouteRequest request) {
        try {
            return getWalkingRouteWithException(request);
        } catch (Exception e) {
            log.error("步行路线规划失败: {}", e.getMessage(), e);
            return WalkingRouteResponse.error("步行路线规划失败: " + e.getMessage(), "50000");
        }
    }

    @Override
    public WalkingRouteResponse getWalkingRouteWithException(RouteRequest request) throws Exception {
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

        // 4. 解析步行API响应
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
    private WalkingRouteResponse parseWalkingApiResponse(Map<String, Object> apiResponse) {
        WalkingRouteResponse response = new WalkingRouteResponse();
        
        // 设置基础状态信息
        response.setStatus((Integer) apiResponse.get("status"));
        response.setInfo((String) apiResponse.get("info"));
        response.setInfocode(String.valueOf(apiResponse.get("infocode")));
        
        if (response.getStatus() != 1) {
            log.error("高德地图步行API调用失败: {}", response.getInfo());
            return response;
        }
        
        // 解析路径数据
        Map<String, Object> routeData = (Map<String, Object>) apiResponse.get("route");
        List<Map<String, Object>> paths = (List<Map<String, Object>>) routeData.get("paths");
        
        response.setCount(paths.size());
        response.setOrigin((String) routeData.get("origin"));
        response.setDestination((String) routeData.get("destination"));
        response.setPaths(parseWalkingPaths(paths));
        
        log.info("步行路线规划成功，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 解析多条步行路径
     */
    @SuppressWarnings("unchecked")
    private List<WalkingPath> parseWalkingPaths(List<Map<String, Object>> paths) {
        List<WalkingPath> walkingPaths = new ArrayList<>();
        
        for (Map<String, Object> pathData : paths) {
            WalkingPath walkingPath = new WalkingPath();
            
            // 设置路径属性
            walkingPath.setDistance((Integer) pathData.get("distance"));
            walkingPath.setDuration((Integer) pathData.get("duration"));
            
            // 解析分段信息
            List<Map<String, Object>> steps = (List<Map<String, Object>>) pathData.get("steps");
            walkingPath.setSteps(parseWalkingSteps(steps));
            
            walkingPaths.add(walkingPath);
        }
        
        return walkingPaths;
    }

    /**
     * 解析步行分段
     */
    @SuppressWarnings("unchecked")
    private List<WalkingStep> parseWalkingSteps(List<Map<String, Object>> steps) {
        List<WalkingStep> walkingSteps = new ArrayList<>();
        
        for (Map<String, Object> stepData : steps) {
            WalkingStep walkingStep = new WalkingStep();
            
            // 设置分段属性
            walkingStep.setInstruction((String) stepData.get("instruction"));
            walkingStep.setRoad((String) stepData.get("road"));
            walkingStep.setDistance((Integer) stepData.get("distance"));
            walkingStep.setOrientation((String) stepData.get("orientation"));
            walkingStep.setDuration((Integer) stepData.get("duration"));
            walkingStep.setPolyline((String) stepData.get("polyline"));
            walkingStep.setAction((String) stepData.get("action"));
            walkingStep.setAssistantAction((String) stepData.get("assistant_action"));
            
            // 处理walk_type字段，可能是字符串或整数
            Object walkTypeObj = stepData.get("walk_type");
            if (walkTypeObj != null) {
                if (walkTypeObj instanceof Integer) {
                    walkingStep.setWalkType((Integer) walkTypeObj);
                } else if (walkTypeObj instanceof String) {
                    try {
                        walkingStep.setWalkType(Integer.parseInt((String) walkTypeObj));
                    } catch (NumberFormatException e) {
                        log.warn("walk_type格式错误: {}", walkTypeObj);
                        walkingStep.setWalkType(0); // 默认普通道路
                    }
                }
            }
            
            walkingSteps.add(walkingStep);
        }
        
        return walkingSteps;
    }

    @Override
    public BicyclingRouteResponse getBicyclingRoute(RouteRequest request) {
        try {
            return getBicyclingRouteWithException(request);
        } catch (Exception e) {
            log.error("骑行路线规划失败: {}", e.getMessage(), e);
            return BicyclingRouteResponse.error("骑行路线规划失败: " + e.getMessage(), "50000");
        }
    }

    @Override
    public BicyclingRouteResponse getBicyclingRouteWithException(RouteRequest request) throws Exception {
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
    private BicyclingRouteResponse parseBicyclingApiResponse(Map<String, Object> apiResponse) {
        BicyclingRouteResponse response = new BicyclingRouteResponse();
        
        // 骑行API使用不同的状态码字段
        Integer errcode = (Integer) apiResponse.get("errcode");
        String errmsg = (String) apiResponse.get("errmsg");
        
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
        
        // 解析数据
        Map<String, Object> data = (Map<String, Object>) apiResponse.get("data");
        if (data != null) {
            List<Map<String, Object>> paths = (List<Map<String, Object>>) data.get("paths");
            
            response.setCount(paths != null ? paths.size() : 0);
            response.setRoute(parseBicyclingPaths(paths));
        } else {
            response.setCount(0);
            response.setRoute(new ArrayList<>());
        }
        
        log.info("骑行路线规划成功，返回 {} 条路径", response.getCount());
        return response;
    }

    /**
     * 解析多条骑行路径
     */
    @SuppressWarnings("unchecked")
    private List<BicyclingPath> parseBicyclingPaths(List<Map<String, Object>> paths) {
        List<BicyclingPath> bicyclingPaths = new ArrayList<>();
        
        if (paths == null) {
            return bicyclingPaths;
        }
        
        for (Map<String, Object> pathData : paths) {
            BicyclingPath bicyclingPath = new BicyclingPath();
            
            // 设置路径属性
            bicyclingPath.setDistance(((Number) pathData.get("distance")).doubleValue());
            bicyclingPath.setDuration(((Number) pathData.get("duration")).doubleValue());
            
            // 解析分段信息
            List<Map<String, Object>> steps = (List<Map<String, Object>>) pathData.get("steps");
            bicyclingPath.setSteps(parseBicyclingSteps(steps));
            
            bicyclingPaths.add(bicyclingPath);
        }
        
        return bicyclingPaths;
    }

    /**
     * 解析骑行分段
     */
    @SuppressWarnings("unchecked")
    private List<BicyclingStep> parseBicyclingSteps(List<Map<String, Object>> steps) {
        List<BicyclingStep> bicyclingSteps = new ArrayList<>();
        
        if (steps == null) {
            return bicyclingSteps;
        }
        
        for (Map<String, Object> stepData : steps) {
            BicyclingStep bicyclingStep = new BicyclingStep();
            
            // 设置分段属性
            bicyclingStep.setInstruction((String) stepData.get("instruction"));
            bicyclingStep.setRoad((String) stepData.get("road"));
            bicyclingStep.setDistance(((Number) stepData.get("distance")).doubleValue());
            bicyclingStep.setOrientation((String) stepData.get("orientation"));
            bicyclingStep.setDuration(((Number) stepData.get("duration")).doubleValue());
            bicyclingStep.setPolyline((String) stepData.get("polyline"));
            bicyclingStep.setAction((String) stepData.get("action"));
            bicyclingStep.setAssistantAction((String) stepData.get("assistant_action"));
            
            // 处理walk_type字段
            Object walkTypeObj = stepData.get("walk_type");
            if (walkTypeObj != null) {
                if (walkTypeObj instanceof Integer) {
                    bicyclingStep.setWalkType((Integer) walkTypeObj);
                } else if (walkTypeObj instanceof String) {
                    try {
                        bicyclingStep.setWalkType(Integer.parseInt((String) walkTypeObj));
                    } catch (NumberFormatException e) {
                        log.warn("walk_type格式错误: {}", walkTypeObj);
                        bicyclingStep.setWalkType(0); // 默认普通道路
                    }
                }
            }
            
            bicyclingSteps.add(bicyclingStep);
        }
        
        return bicyclingSteps;
    }
}