package com.backend.be.service.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.backend.be.mapper.FeatureDetailMapper;
import com.backend.be.model.FeatureDetailRequest;
import com.backend.be.model.FeatureDetailResponse;
import com.backend.be.service.FeatureDetailService;

/**
 * 要素详情服务实现类
 */
@Service
public class FeatureDetailServiceImpl implements FeatureDetailService {

    @Autowired
    private FeatureDetailMapper featureDetailMapper;

    @Override
    public FeatureDetailResponse getFeatureDetail(FeatureDetailRequest request) {
        // 验证请求参数
        if (!request.isValid()) {
            return FeatureDetailResponse.error(request.getTableName(), request.getFeatureId(), 
                    "请求参数无效：表名和要素ID不能为空");
        }

        String tableName = request.getTableName();
        String featureId = request.getFeatureId();

        // 检查表是否存在
        if (!tableExists(tableName)) {
            return FeatureDetailResponse.error(tableName, featureId, 
                    "表 '" + tableName + "' 不存在");
        }

        // 检查要素是否存在
        if (!featureExists(tableName, featureId)) {
            return FeatureDetailResponse.error(tableName, featureId, 
                    "要素 '" + featureId + "' 在表 '" + tableName + "' 中不存在");
        }

        try {
            // 获取要素详情
            Map<String, Object> featureData = featureDetailMapper.getFeatureDetail(tableName, featureId);
            
            if (featureData == null || featureData.isEmpty()) {
                return FeatureDetailResponse.error(tableName, featureId, 
                        "获取要素详情失败");
            }

            // 处理图片URL
            List<String> imageUrls = extractImageUrls(featureData, request.getImageFields());
            
            // 过滤字段（如果指定了字段列表）
            Map<String, Object> filteredAttributes = filterAttributes(featureData, request.getFields());

            return FeatureDetailResponse.success(tableName, featureId, filteredAttributes, imageUrls);

        } catch (Exception e) {
            return FeatureDetailResponse.error(tableName, featureId, 
                    "查询要素详情时发生错误: " + e.getMessage());
        }
    }

    @Override
    public FeatureDetailResponse getFeatureDetail(String tableName, String featureId) {
        FeatureDetailRequest request = new FeatureDetailRequest(tableName, featureId);
        return getFeatureDetail(request);
    }

    @Override
    public boolean tableExists(String tableName) {
        try {
            return featureDetailMapper.tableExists(tableName);
        } catch (Exception e) {
            return false;
        }
    }

    @Override
    public boolean featureExists(String tableName, String featureId) {
        try {
            return featureDetailMapper.featureExists(tableName, featureId);
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * 从要素数据中提取图片URL
     * @param featureData 要素数据
     * @param imageFields 图片字段名数组
     * @return 图片URL列表
     */
    private List<String> extractImageUrls(Map<String, Object> featureData, String[] imageFields) {
        List<String> imageUrls = new ArrayList<>();
        
        if (imageFields != null && imageFields.length > 0) {
            for (String field : imageFields) {
                Object value = featureData.get(field);
                if (value != null && value instanceof String) {
                    String url = ((String) value).trim();
                    if (!url.isEmpty() && isImageUrl(url)) {
                        imageUrls.add(url);
                    }
                }
            }
        } else {
            // 如果没有指定图片字段，自动检测可能的图片字段
            for (Map.Entry<String, Object> entry : featureData.entrySet()) {
                if (entry.getValue() instanceof String) {
                    String value = ((String) entry.getValue()).trim();
                    if (isImageUrl(value)) {
                        imageUrls.add(value);
                    }
                }
            }
        }
        
        return imageUrls;
    }

    /**
     * 过滤属性字段
     * @param featureData 原始要素数据
     * @param fields 需要返回的字段列表
     * @return 过滤后的属性数据
     */
    private Map<String, Object> filterAttributes(Map<String, Object> featureData, String[] fields) {
        if (fields == null || fields.length == 0) {
            // 如果没有指定字段，返回所有字段（排除几何字段）
            Map<String, Object> filtered = new HashMap<>();
            for (Map.Entry<String, Object> entry : featureData.entrySet()) {
                String key = entry.getKey();
                // 排除几何字段
                if (!isGeometryField(key)) {
                    filtered.put(key, entry.getValue());
                }
            }
            return filtered;
        } else {
            // 只返回指定的字段
            Map<String, Object> filtered = new HashMap<>();
            for (String field : fields) {
                if (featureData.containsKey(field)) {
                    filtered.put(field, featureData.get(field));
                }
            }
            return filtered;
        }
    }

    /**
     * 判断是否为图片URL
     * @param url URL字符串
     * @return true 如果是图片URL
     */
    private boolean isImageUrl(String url) {
        if (url == null || url.trim().isEmpty()) {
            return false;
        }
        
        String lowerUrl = url.toLowerCase();
        return lowerUrl.startsWith("http") && 
               (lowerUrl.endsWith(".jpg") || lowerUrl.endsWith(".jpeg") || 
                lowerUrl.endsWith(".png") || lowerUrl.endsWith(".gif") ||
                lowerUrl.endsWith(".bmp") || lowerUrl.endsWith(".webp") ||
                lowerUrl.contains("/images/") || lowerUrl.contains("/img/"));
    }

    /**
     * 判断是否为几何字段
     * @param fieldName 字段名
     * @return true 如果是几何字段
     */
    private boolean isGeometryField(String fieldName) {
        String lowerField = fieldName.toLowerCase();
        return lowerField.equals("geom") || lowerField.equals("geometry") || 
               lowerField.equals("element_location") || lowerField.equals("shape") ||
               lowerField.endsWith("_geom") || lowerField.endsWith("_geometry");
    }
}
