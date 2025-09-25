package com.backend.be.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.backend.be.pojo.User;

@Repository
public interface UserRepository extends JpaRepository<User, Integer>, JpaSpecificationExecutor<User> {
    
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
     * 自定义查询：根据用户名前缀查询
     * @param prefix 用户名前缀
     * @return 用户列表
     */
    @Query("SELECT u FROM User u WHERE u.username LIKE :prefix%")
    List<User> findByUsernameStartingWith(@Param("prefix") String prefix);
    
    /**
     * 自定义查询：统计用户数量
     * @return 用户总数
     */
    @Query("SELECT COUNT(u) FROM User u")
    long countAllUsers();
    
    /**
     * 自定义查询：获取所有用户并按用户名排序
     * @return 排序后的用户列表
     */
    @Query("SELECT u FROM User u ORDER BY u.username ASC")
    List<User> findAllOrderByUsername();
}
