package com.backend.be.service;

import java.util.List;
import java.util.Optional;

import com.backend.be.pojo.User;

public interface IUserService {
    User createUser(User user);
    
    /**
     * 根据用户名查找用户
     * @param username 用户名
     * @return 用户信息
     */
    Optional<User> findByUsername(String username);
    
    /**
     * 根据用户名模糊查询
     * @param username 用户名（模糊匹配）
     * @return 用户列表
     */
    List<User> findByUsernameContaining(String username);
    
    /**
     * 检查用户名是否存在
     * @param username 用户名
     * @return 是否存在
     */
    boolean existsByUsername(String username);
    
    /**
     * 根据用户名和密码查询用户（用于登录验证）
     * @param username 用户名
     * @param password 密码
     * @return 用户信息
     */
    Optional<User> findByUsernameAndPassword(String username, String password);
    
    /**
     * 获取所有用户
     * @return 用户列表
     */
    List<User> findAll();
    
    /**
     * 根据ID查找用户
     * @param id 用户ID
     * @return 用户信息
     */
    Optional<User> findById(Integer id);
    
    /**
     * 更新用户信息
     * @param user 用户信息
     * @return 更新后的用户
     */
    User updateUser(User user);
    
    /**
     * 删除用户
     * @param id 用户ID
     */
    void deleteUser(Integer id);
    
    /**
     * 统计用户数量
     * @return 用户总数
     */
    long countUsers();
    
    /**
     * 获取所有用户并按用户名排序
     * @return 排序后的用户列表
     */
    List<User> findAllOrderByUsername();
}
