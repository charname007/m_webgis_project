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

    @Override
    public boolean updateByName(com.backend.be.model.ASight aSight) {
        try {
            int result = sightMapper.updateByName(aSight);
            System.out.println("景区更新成功 - 名称: " + aSight.getName() + ", 影响行数: " + result);
            return result > 0;
        } catch (Exception e) {
            System.err.println("景区更新失败 - 名称: " + aSight.getName() + ", 错误详情: " + e.getMessage());
            e.printStackTrace(); // 打印完整的堆栈跟踪
            return false;
        }
    }

    @Override
    public boolean upsertByName(com.backend.be.model.ASight aSight) {
        try {
            // 先尝试更新，如果更新失败则插入
            System.out.println("开始upsert操作 - 名称: " + aSight.getName() + ", 数据: " + aSight.toString());
            System.out.println("坐标信息 - lngWgs84: " + aSight.getLngWgs84() + ", latWgs84: " + aSight.getLatWgs84());
            
            // 使用部分更新，只更新非null字段，避免覆盖现有数据
            int updateResult = sightMapper.updateByNameSelective(aSight);
            System.out.println("部分更新操作结果 - 影响行数: " + updateResult);
            
            if (updateResult > 0) {
                System.out.println("景区upsert成功 - 名称: " + aSight.getName() + ", 部分更新影响行数: " + updateResult);
                return true;
            } else {
                // 更新失败，尝试插入
                System.out.println("部分更新失败，尝试插入 - 名称: " + aSight.getName());
                int insertResult = sightMapper.insert(aSight);
                System.out.println("插入操作结果 - 影响行数: " + insertResult);
                
                if (insertResult > 0) {
                    System.out.println("景区upsert成功 - 名称: " + aSight.getName() + ", 插入影响行数: " + insertResult);
                    return true;
                } else {
                    System.err.println("景区upsert失败 - 名称: " + aSight.getName() + ", 插入失败，可能原因：名称冲突、数据约束等");
                    return false;
                }
            }
        } catch (Exception e) {
            System.err.println("景区upsert失败 - 名称: " + aSight.getName() + ", 错误详情: " + e.getMessage());
            e.printStackTrace(); // 打印完整的堆栈跟踪
            return false;
        }
    }

    @Override
    public boolean insert(com.backend.be.model.ASight aSight) {
        try {
            int result = sightMapper.insert(aSight);
            System.out.println("景区插入成功 - 名称: " + aSight.getName() + ", 影响行数: " + result);
            return result > 0;
        } catch (Exception e) {
            System.err.println("景区插入失败 - 名称: " + aSight.getName() + ", 错误详情: " + e.getMessage());
            e.printStackTrace(); // 打印完整的堆栈跟踪
            return false;
        }
    }
}
