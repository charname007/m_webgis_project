package com.backend.be.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import com.backend.be.pojo.User;
import com.backend.be.repository.UserRepository;

import jakarta.persistence.criteria.Predicate;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 通用查询服务类
 * 提供高级查询功能，如分页、排序、条件查询等
 */
@Service
public class QueryService {

    @Autowired
    private UserRepository userRepository;

    /**
     * 通用分页查询
     * @param page 页码（从0开始）
     * @param size 每页大小
     * @return 分页结果
     */
    public Page<User> findAllUsersWithPagination(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return userRepository.findAll(pageable);
    }

    /**
     * 带排序的分页查询
     * @param page 页码
     * @param size 每页大小
     * @param sortField 排序字段
     * @param sortDirection 排序方向（ASC/DESC）
     * @return 分页结果
     */
    public Page<User> findAllUsersWithPaginationAndSort(int page, int size, String sortField, String sortDirection) {
        Sort sort = sortDirection.equalsIgnoreCase("DESC") 
            ? Sort.by(sortField).descending() 
            : Sort.by(sortField).ascending();
        Pageable pageable = PageRequest.of(page, size, sort);
        return userRepository.findAll(pageable);
    }

    /**
     * 动态条件查询
     * @param criteria 查询条件Map
     * @return 符合条件的用户列表
     */
    public List<User> findUsersByCriteria(Map<String, Object> criteria) {
        Specification<User> specification = (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();
            
            // 用户名模糊查询
            if (criteria.containsKey("username")) {
                predicates.add(criteriaBuilder.like(root.get("username"), "%" + criteria.get("username") + "%"));
            }
            
            // ID精确查询
            if (criteria.containsKey("id")) {
                predicates.add(criteriaBuilder.equal(root.get("id"), criteria.get("id")));
            }
            
            // 可以继续添加其他字段的查询条件
            
            return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
        };
        
        return userRepository.findAll(specification);
    }

    /**
     * 动态条件分页查询
     * @param criteria 查询条件Map
     * @param page 页码
     * @param size 每页大小
     * @param sortField 排序字段
     * @param sortDirection 排序方向
     * @return 分页结果
     */
    public Page<User> findUsersByCriteriaWithPagination(Map<String, Object> criteria, int page, int size, String sortField, String sortDirection) {
        Specification<User> specification = (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();
            
            if (criteria.containsKey("username")) {
                predicates.add(criteriaBuilder.like(root.get("username"), "%" + criteria.get("username") + "%"));
            }
            
            if (criteria.containsKey("id")) {
                predicates.add(criteriaBuilder.equal(root.get("id"), criteria.get("id")));
            }
            
            return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
        };
        
        Sort sort = sortDirection.equalsIgnoreCase("DESC") 
            ? Sort.by(sortField).descending() 
            : Sort.by(sortField).ascending();
        Pageable pageable = PageRequest.of(page, size, sort);
        
        return userRepository.findAll(specification, pageable);
    }

    /**
     * 统计查询
     * @param criteria 查询条件
     * @return 符合条件的记录数
     */
    public long countUsersByCriteria(Map<String, Object> criteria) {
        Specification<User> specification = (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();
            
            if (criteria.containsKey("username")) {
                predicates.add(criteriaBuilder.like(root.get("username"), "%" + criteria.get("username") + "%"));
            }
            
            if (criteria.containsKey("id")) {
                predicates.add(criteriaBuilder.equal(root.get("id"), criteria.get("id")));
            }
            
            return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
        };
        
        return userRepository.count(specification);
    }

    /**
     * 检查是否存在符合条件的记录
     * @param criteria 查询条件
     * @return 是否存在
     */
    public boolean existsByCriteria(Map<String, Object> criteria) {
        Specification<User> specification = (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();
            
            if (criteria.containsKey("username")) {
                predicates.add(criteriaBuilder.like(root.get("username"), "%" + criteria.get("username") + "%"));
            }
            
            if (criteria.containsKey("id")) {
                predicates.add(criteriaBuilder.equal(root.get("id"), criteria.get("id")));
            }
            
            return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
        };
        
        return userRepository.exists(specification);
    }

    /**
     * 获取用户名列表（去重）
     * @return 所有不重复的用户名
     */
    public List<String> findAllDistinctUsernames() {
        return userRepository.findAll().stream()
                .map(User::getUsername)
                .distinct()
                .toList();
    }

    /**
     * 批量查询用户
     * @param ids 用户ID列表
     * @return 用户列表
     */
    public List<User> findUsersByIds(List<Integer> ids) {
        return userRepository.findAllById(ids);
    }

    /**
     * 获取用户统计信息
     * @return 统计信息Map
     */
    public Map<String, Object> getUserStatistics() {
        long totalUsers = userRepository.count();
        List<User> allUsers = userRepository.findAll();
        
        // 可以添加更多统计信息
        return Map.of(
            "totalUsers", totalUsers,
            "sampleUsernames", allUsers.stream()
                .limit(5)
                .map(User::getUsername)
                .toList()
        );
    }
}
