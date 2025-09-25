package com.backend.be.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.backend.be.pojo.ResponseMessage;
import com.backend.be.pojo.User;
import com.backend.be.service.QueryService;

/**
 * 高级查询控制器
 * 提供分页、排序、条件查询等高级功能
 */
@RestController
@RequestMapping("/query")
public class QueryController {

    @Autowired
    private QueryService queryService;

    /**
     * 分页查询所有用户
     * @param page 页码（从0开始）
     * @param size 每页大小
     * @return 分页结果
     */
    @GetMapping("/users/paged")
    public String findAllUsersWithPagination(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        try {
            Page<User> result = queryService.findAllUsersWithPagination(page, size);
            Map<String, Object> response = new HashMap<>();
            response.put("content", result.getContent());
            response.put("totalPages", result.getTotalPages());
            response.put("totalElements", result.getTotalElements());
            response.put("currentPage", result.getNumber());
            response.put("pageSize", result.getSize());
            return ResponseMessage.success(response).toString();
        } catch (Exception e) {
            return ResponseMessage.error("查询失败: " + e.getMessage()).toString();
        }
    }

    /**
     * 带排序的分页查询
     * @param page 页码
     * @param size 每页大小
     * @param sortField 排序字段
     * @param sortDirection 排序方向
     * @return 分页结果
     */
    @GetMapping("/users/paged-sorted")
    public String findAllUsersWithPaginationAndSort(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "username") String sortField,
            @RequestParam(defaultValue = "ASC") String sortDirection) {
        try {
            Page<User> result = queryService.findAllUsersWithPaginationAndSort(page, size, sortField, sortDirection);
            Map<String, Object> response = new HashMap<>();
            response.put("content", result.getContent());
            response.put("totalPages", result.getTotalPages());
            response.put("totalElements", result.getTotalElements());
            response.put("currentPage", result.getNumber());
            response.put("pageSize", result.getSize());
            response.put("sortField", sortField);
            response.put("sortDirection", sortDirection);
            return ResponseMessage.success(response).toString();
        } catch (Exception e) {
            return ResponseMessage.error("查询失败: " + e.getMessage()).toString();
        }
    }

    /**
     * 动态条件查询
     * @param username 用户名（模糊匹配）
     * @param id 用户ID（精确匹配）
     * @return 符合条件的用户列表
     */
    @GetMapping("/users/by-criteria")
    public String findUsersByCriteria(
            @RequestParam(required = false) String username,
            @RequestParam(required = false) Integer id) {
        try {
            Map<String, Object> criteria = new HashMap<>();
            if (username != null) {
                criteria.put("username", username);
            }
            if (id != null) {
                criteria.put("id", id);
            }
            
            List<User> users = queryService.findUsersByCriteria(criteria);
            return ResponseMessage.success(users).toString();
        } catch (Exception e) {
            return ResponseMessage.error("查询失败: " + e.getMessage()).toString();
        }
    }

    /**
     * 动态条件分页查询
     * @param username 用户名
     * @param id 用户ID
     * @param page 页码
     * @param size 每页大小
     * @param sortField 排序字段
     * @param sortDirection 排序方向
     * @return 分页结果
     */
    @GetMapping("/users/paged-criteria")
    public String findUsersByCriteriaWithPagination(
            @RequestParam(required = false) String username,
            @RequestParam(required = false) Integer id,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "username") String sortField,
            @RequestParam(defaultValue = "ASC") String sortDirection) {
        try {
            Map<String, Object> criteria = new HashMap<>();
            if (username != null) {
                criteria.put("username", username);
            }
            if (id != null) {
                criteria.put("id", id);
            }
            
            Page<User> result = queryService.findUsersByCriteriaWithPagination(criteria, page, size, sortField, sortDirection);
            Map<String, Object> response = new HashMap<>();
            response.put("content", result.getContent());
            response.put("totalPages", result.getTotalPages());
            response.put("totalElements", result.getTotalElements());
            response.put("currentPage", result.getNumber());
            response.put("pageSize", result.getSize());
            response.put("criteria", criteria);
            return ResponseMessage.success(response).toString();
        } catch (Exception e) {
            return ResponseMessage.error("查询失败: " + e.getMessage()).toString();
        }
    }

    /**
     * 统计查询
     * @param username 用户名
     * @param id 用户ID
     * @return 符合条件的记录数
     */
    @GetMapping("/users/count")
    public String countUsersByCriteria(
            @RequestParam(required = false) String username,
            @RequestParam(required = false) Integer id) {
        try {
            Map<String, Object> criteria = new HashMap<>();
            if (username != null) {
                criteria.put("username", username);
            }
            if (id != null) {
                criteria.put("id", id);
            }
            
            long count = queryService.countUsersByCriteria(criteria);
            return ResponseMessage.success(count).toString();
        } catch (Exception e) {
            return ResponseMessage.error("统计失败: " + e.getMessage()).toString();
        }
    }

    /**
     * 检查是否存在符合条件的记录
     * @param username 用户名
     * @param id 用户ID
     * @return 是否存在
     */
    @GetMapping("/users/exists")
    public String existsByCriteria(
            @RequestParam(required = false) String username,
            @RequestParam(required = false) Integer id) {
        try {
            Map<String, Object> criteria = new HashMap<>();
            if (username != null) {
                criteria.put("username", username);
            }
            if (id != null) {
                criteria.put("id", id);
            }
            
            boolean exists = queryService.existsByCriteria(criteria);
            return ResponseMessage.success(exists).toString();
        } catch (Exception e) {
            return ResponseMessage.error("检查失败: " + e.getMessage()).toString();
        }
    }

    /**
     * 获取所有不重复的用户名
     * @return 用户名列表
     */
    @GetMapping("/users/distinct-usernames")
    public String findAllDistinctUsernames() {
        try {
            List<String> usernames = queryService.findAllDistinctUsernames();
            return ResponseMessage.success(usernames).toString();
        } catch (Exception e) {
            return ResponseMessage.error("查询失败: " + e.getMessage()).toString();
        }
    }

    /**
     * 批量查询用户
     * @param ids 用户ID列表（逗号分隔）
     * @return 用户列表
     */
    @GetMapping("/users/batch")
    public String findUsersByIds(@RequestParam String ids) {
        try {
            List<Integer> idList = List.of(ids.split(","))
                    .stream()
                    .map(Integer::parseInt)
                    .toList();
            List<User> users = queryService.findUsersByIds(idList);
            return ResponseMessage.success(users).toString();
        } catch (Exception e) {
            return ResponseMessage.error("批量查询失败: " + e.getMessage()).toString();
        }
    }

    /**
     * 获取用户统计信息
     * @return 统计信息
     */
    @GetMapping("/users/statistics")
    public String getUserStatistics() {
        try {
            Map<String, Object> statistics = queryService.getUserStatistics();
            return ResponseMessage.success(statistics).toString();
        } catch (Exception e) {
            return ResponseMessage.error("获取统计信息失败: " + e.getMessage()).toString();
        }
    }
}
