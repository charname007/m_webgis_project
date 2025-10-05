package com.backend.be.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.backend.be.service.ASightService;

@RestController
@RequestMapping("/postgis/WGP_db")
public class ASightController {

    @Autowired
    private ASightService sightService;

    /**
     * 查询指定范围内的景区要素并返回 GeoJSON
     * @param request 景区查询请求参数
     * @return GeoJSON 格式的景区要素集合
     */
    @PostMapping("/tables/a_sight/geojson/extent-level")
    public String getSightGeojsonByExtentAndLevel(
        @RequestBody com.backend.be.model.SightQueryRequest request) {
        return sightService.getSightGeojsonByExtentAndLevel(request);
    }
}
