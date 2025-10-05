package com.backend.be.service.impl;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.backend.be.mapper.ASightMapper;
import com.backend.be.service.ASightService;

@Service
public class ASightServiceImpl implements ASightService {

    @Autowired
    private ASightMapper sightMapper;

    @Override
    public String getSightGeojsonByExtentAndLevel(com.backend.be.model.SightQueryRequest request) {
        // 调用 Mapper 进行景区查询
        try {
            String result = sightMapper.getSightGeojsonByExtentAndLevel(request);
            System.out.println("景区查询成功 - 范围: " + request.getExtentDescription() + ", 等级: " + request.getLevelsDescription());
            return result;
        } catch (Exception e) {
            System.err.println("景区查询失败 - 范围: " + request.getExtentDescription() + ", 等级: " + request.getLevelsDescription() + ", 错误: " + e.getMessage());
            throw new RuntimeException("景区查询失败: " + e.getMessage(), e);
        }
    }
}
