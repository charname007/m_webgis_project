package com.backend.be.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.backend.be.model.TouristSpot;
import com.backend.be.service.TouristSpotService;

/**
 * TouristSpot REST API 控制器
 */
@RestController
@RequestMapping("/api/tourist-spots")
@CrossOrigin(origins = "*")
public class TouristSpotController {

    @Autowired
    private TouristSpotService touristSpotService;

    /**
     * 获取所有旅游景点
     */
    @GetMapping
    public ResponseEntity<List<TouristSpot>> getAllTouristSpots() {
        List<TouristSpot> touristSpots = touristSpotService.getAllTouristSpots();
        return ResponseEntity.ok(touristSpots);
    }

    /**
     * 根据ID获取旅游景点
     */
    @GetMapping("/{id}")
    public ResponseEntity<TouristSpot> getTouristSpotById(@PathVariable Integer id) {
        TouristSpot touristSpot = touristSpotService.getTouristSpotById(id);
        if (touristSpot != null) {
            return ResponseEntity.ok(touristSpot);
        } else {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 根据城市获取旅游景点
     */
    @GetMapping("/city/{city}")
    public ResponseEntity<List<TouristSpot>> getTouristSpotsByCity(@PathVariable String city) {
        List<TouristSpot> touristSpots = touristSpotService.getTouristSpotsByCity(city);
        return ResponseEntity.ok(touristSpots);
    }

    /**
     * 根据名称搜索旅游景点（查询参数方式）
     */
    @GetMapping("/search")
    public ResponseEntity<List<TouristSpot>> searchTouristSpotsByName(@RequestParam String name) {
        List<TouristSpot> touristSpots = touristSpotService.searchTouristSpotsByName(name);
        return ResponseEntity.ok(touristSpots);
    }

    /**
     * 根据名称查询旅游景点（路径参数方式，支持模糊匹配）
     */
    @GetMapping("/name/{name}")
    public ResponseEntity<List<TouristSpot>> getTouristSpotsByName(@PathVariable String name) {
        List<TouristSpot> touristSpots = touristSpotService.searchTouristSpotsByName(name);
        return ResponseEntity.ok(touristSpots);
    }

    /**
     * 创建旅游景点
     */
    @PostMapping
    public ResponseEntity<TouristSpot> createTouristSpot(@RequestBody TouristSpot touristSpot) {
        TouristSpot createdTouristSpot = touristSpotService.createTouristSpot(touristSpot);
        if (createdTouristSpot != null) {
            return ResponseEntity.ok(createdTouristSpot);
        } else {
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * 更新旅游景点
     */
    @PutMapping("/{id}")
    public ResponseEntity<TouristSpot> updateTouristSpot(@PathVariable Integer id, @RequestBody TouristSpot touristSpot) {
        touristSpot.setId(id);
        TouristSpot updatedTouristSpot = touristSpotService.updateTouristSpot(touristSpot);
        if (updatedTouristSpot != null) {
            return ResponseEntity.ok(updatedTouristSpot);
        } else {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 更新旅游景点和关联的景区信息（双表更新）
     */
    @PutMapping("/{id}/with-sight")
    public ResponseEntity<TouristSpot> updateTouristSpotWithSight(
            @PathVariable Integer id, 
            @RequestBody com.backend.be.model.TouristSpotUpdateRequest updateRequest) {
        
        // 设置 tourist_spot 的 ID（如果id为0，表示通过名称更新）
        if (updateRequest.getTourist_spot() != null && id != 0) {
            updateRequest.getTourist_spot().setId(id);
        }
        
        // 处理a_sight表的名称，提取中文部分
        if (updateRequest.getA_sight() != null && updateRequest.getA_sight().getName() != null) {
            String chineseName = extractChineseName(updateRequest.getA_sight().getName());
            updateRequest.getA_sight().setName(chineseName);
        }
        
        TouristSpot updatedTouristSpot = touristSpotService.updateTouristSpotWithSight(updateRequest);
        if (updatedTouristSpot != null) {
            return ResponseEntity.ok(updatedTouristSpot);
        } else {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 通过名称更新旅游景点和关联的景区信息（双表更新）- 部分更新版本
     */
    @PutMapping("/by-name/{name}/with-sight")
    public ResponseEntity<TouristSpot> updateTouristSpotByNameWithSight(
            @PathVariable String name, 
            @RequestBody com.backend.be.model.TouristSpotUpdateRequest updateRequest) {
        
        // 提取中文名称（去除英文部分）
        String chineseName = extractChineseName(name);
        
        // 设置 tourist_spot 的名称
        if (updateRequest.getTourist_spot() != null) {
            updateRequest.getTourist_spot().setName(chineseName);
        }
        
        // 设置 a_sight 的名称
        if (updateRequest.getA_sight() != null) {
            updateRequest.getA_sight().setName(chineseName);
        }
        
        TouristSpot updatedTouristSpot = touristSpotService.updateTouristSpotByNameWithSight(updateRequest);
        if (updatedTouristSpot != null) {
            return ResponseEntity.ok(updatedTouristSpot);
        } else {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 从混合名称中提取中文部分
     * 例如："武汉大学Wuhan University" -> "武汉大学"
     * @param mixedName 混合名称
     * @return 中文名称
     */
    private String extractChineseName(String mixedName) {
        if (mixedName == null || mixedName.trim().isEmpty()) {
            return mixedName;
        }
        
        // 使用正则表达式匹配中文部分
        // 匹配所有中文字符，直到遇到第一个非中文字符
        java.util.regex.Pattern pattern = java.util.regex.Pattern.compile("^[\u4e00-\u9fa5]+\s*[\u4e00-\u9fa5]*");
        java.util.regex.Matcher matcher = pattern.matcher(mixedName);
        
        if (matcher.find()) {
            String chinesePart = matcher.group().trim();
            if (!chinesePart.isEmpty()) {
                return chinesePart;
            }
        }
        
        // 如果没有找到中文部分，返回原名称
        return mixedName;
    }

    /**
     * 删除旅游景点
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteTouristSpot(@PathVariable Integer id) {
        boolean deleted = touristSpotService.deleteTouristSpot(id);
        if (deleted) {
            return ResponseEntity.ok().build();
        } else {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 获取旅游景点总数
     */
    @GetMapping("/count")
    public ResponseEntity<Integer> getTouristSpotCount() {
        int count = touristSpotService.getTouristSpotCount();
        return ResponseEntity.ok(count);
    }
}
