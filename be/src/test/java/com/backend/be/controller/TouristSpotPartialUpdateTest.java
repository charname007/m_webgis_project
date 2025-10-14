package com.backend.be.controller;

import com.backend.be.model.TouristSpot;
import com.backend.be.model.TouristSpotUpdateRequest;
import com.backend.be.model.ASight;
import com.backend.be.service.TouristSpotService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;

/**
 * 旅游景点部分更新功能测试
 */
@ExtendWith(SpringExtension.class)
@WebMvcTest(TouristSpotController.class)
public class TouristSpotPartialUpdateTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private TouristSpotService touristSpotService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    public void testPartialUpdateOnlyName() throws Exception {
        // 创建部分更新的请求 - 只更新名称
        TouristSpotUpdateRequest updateRequest = new TouristSpotUpdateRequest();
        
        TouristSpot touristSpot = new TouristSpot();
        touristSpot.setName("测试景点"); // 只设置名称，其他字段为null
        
        ASight aSight = new ASight();
        aSight.setName("测试景点");
        
        updateRequest.setTourist_spot(touristSpot);
        updateRequest.setA_sight(aSight);

        // 模拟服务返回
        TouristSpot updatedSpot = new TouristSpot();
        updatedSpot.setId(1);
        updatedSpot.setName("测试景点");
        updatedSpot.set地址("原始地址"); // 其他字段保持原值
        updatedSpot.set介绍("原始介绍");
        
        when(touristSpotService.updateTouristSpotByNameWithSight(any(TouristSpotUpdateRequest.class)))
                .thenReturn(updatedSpot);

        // 执行测试
        mockMvc.perform(put("/api/tourist-spots/by-name/测试景点OldName/with-sight")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(updateRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("测试景点"))
                .andExpect(jsonPath("$.地址").value("原始地址")); // 验证其他字段未被覆盖
    }

    @Test
    public void testPartialUpdateOnlyAddress() throws Exception {
        // 创建部分更新的请求 - 只更新地址
        TouristSpotUpdateRequest updateRequest = new TouristSpotUpdateRequest();
        
        TouristSpot touristSpot = new TouristSpot();
        touristSpot.setName("武汉大学"); // 保持名称不变
        touristSpot.set地址("新地址123号"); // 只更新地址
        
        updateRequest.setTourist_spot(touristSpot);
        updateRequest.setA_sight(null); // 不更新a_sight

        // 模拟服务返回
        TouristSpot updatedSpot = new TouristSpot();
        updatedSpot.setId(1);
        updatedSpot.setName("武汉大学"); // 名称保持不变
        updatedSpot.set地址("新地址123号"); // 地址已更新
        updatedSpot.set介绍("原始介绍"); // 其他字段保持不变
        
        when(touristSpotService.updateTouristSpotByNameWithSight(any(TouristSpotUpdateRequest.class)))
                .thenReturn(updatedSpot);

        // 执行测试
        mockMvc.perform(put("/api/tourist-spots/by-name/武汉大学Wuhan University/with-sight")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(updateRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("武汉大学"))
                .andExpect(jsonPath("$.地址").value("新地址123号"));
    }

    @Test
    public void testPartialUpdateMultipleFields() throws Exception {
        // 创建部分更新的请求 - 更新多个字段
        TouristSpotUpdateRequest updateRequest = new TouristSpotUpdateRequest();
        
        TouristSpot touristSpot = new TouristSpot();
        touristSpot.setName("黄鹤楼");
        touristSpot.set地址("武汉市武昌区新地址");
        touristSpot.set评分("5.0");
        // 不设置介绍、开放时间等其他字段
        
        updateRequest.setTourist_spot(touristSpot);
        updateRequest.setA_sight(null);

        // 模拟服务返回
        TouristSpot updatedSpot = new TouristSpot();
        updatedSpot.setId(1);
        updatedSpot.setName("黄鹤楼");
        updatedSpot.set地址("武汉市武昌区新地址");
        updatedSpot.set评分("5.0");
        updatedSpot.set介绍("原始介绍"); // 未更新的字段保持原值
        updatedSpot.set开放时间("原始开放时间");
        
        when(touristSpotService.updateTouristSpotByNameWithSight(any(TouristSpotUpdateRequest.class)))
                .thenReturn(updatedSpot);

        // 执行测试
        mockMvc.perform(put("/api/tourist-spots/by-name/黄鹤楼Yellow Crane Tower/with-sight")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(updateRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("黄鹤楼"))
                .andExpect(jsonPath("$.地址").value("武汉市武昌区新地址"))
                .andExpect(jsonPath("$.评分").value("5.0"))
                .andExpect(jsonPath("$.介绍").value("原始介绍")); // 验证未更新字段保持不变
    }
}
