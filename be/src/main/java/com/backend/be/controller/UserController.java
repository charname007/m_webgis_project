package com.backend.be.controller;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.backend.be.pojo.ResponseMessage;
import com.backend.be.pojo.User;
import com.backend.be.service.UserService;

@RestController
@RequestMapping("/user")
public class UserController {

    @Autowired
    UserService userService;

    /**
     * 创建用户
     * @param user 用户信息
     * @return 创建结果
     */
    @PostMapping
    public String createUser(@RequestBody User user) {
        User createdUser = userService.createUser(user);
        return ResponseMessage.success(createdUser).toString();
    }

    /**
     * 根据用户名查找用户
     * @param username 用户名
     * @return 用户信息
     */
    @GetMapping("/username/{username}")
    public String findByUsername(@PathVariable String username) {
        Optional<User> user = userService.findByUsername(username);
        if (user.isPresent()) {
            return ResponseMessage.success(user.get()).toString();
        } else {
            return ResponseMessage.error("用户不存在").toString();
        }
    }

    /**
     * 根据用户名模糊查询
     * @param username 用户名（模糊匹配）
     * @return 用户列表
     */
    @GetMapping("/search")
    public String findByUsernameContaining(@RequestParam String username) {
        List<User> users = userService.findByUsernameContaining(username);
        return ResponseMessage.success(users).toString();
    }

    /**
     * 检查用户名是否存在
     * @param username 用户名
     * @return 是否存在
     */
    @GetMapping("/exists/{username}")
    public String existsByUsername(@PathVariable String username) {
        boolean exists = userService.existsByUsername(username);
        return ResponseMessage.success(exists).toString();
    }

    /**
     * 用户登录验证
     * @param username 用户名
     * @param password 密码
     * @return 登录结果
     */
    @PostMapping("/login")
    public String login(@RequestParam String username, @RequestParam String password) {
        Optional<User> user = userService.findByUsernameAndPassword(username, password);
        if (user.isPresent()) {
            return ResponseMessage.success(user.get()).toString();
        } else {
            return ResponseMessage.error("用户名或密码错误").toString();
        }
    }

    /**
     * 获取所有用户
     * @return 用户列表
     */
    @GetMapping("/all")
    public String findAll() {
        List<User> users = userService.findAll();
        return ResponseMessage.success(users).toString();
    }

    /**
     * 根据ID查找用户
     * @param id 用户ID
     * @return 用户信息
     */
    @GetMapping("/{id}")
    public String findById(@PathVariable Integer id) {
        Optional<User> user = userService.findById(id);
        if (user.isPresent()) {
            return ResponseMessage.success(user.get()).toString();
        } else {
            return ResponseMessage.error("用户不存在").toString();
        }
    }

    /**
     * 更新用户信息
     * @param user 用户信息
     * @return 更新结果
     */
    @PutMapping
    public String updateUser(@RequestBody User user) {
        try {
            User updatedUser = userService.updateUser(user);
            return ResponseMessage.success(updatedUser).toString();
        } catch (RuntimeException e) {
            return ResponseMessage.error(e.getMessage()).toString();
        }
    }

    /**
     * 删除用户
     * @param id 用户ID
     * @return 删除结果
     */
    @DeleteMapping("/{id}")
    public String deleteUser(@PathVariable Integer id) {
        try {
            userService.deleteUser(id);
            return ResponseMessage.success("用户删除成功").toString();
        } catch (RuntimeException e) {
            return ResponseMessage.error(e.getMessage()).toString();
        }
    }

    /**
     * 统计用户数量
     * @return 用户总数
     */
    @GetMapping("/count")
    public String countUsers() {
        long count = userService.countUsers();
        return ResponseMessage.success(count).toString();
    }

    /**
     * 获取所有用户并按用户名排序
     * @return 排序后的用户列表
     */
    @GetMapping("/sorted")
    public String findAllOrderByUsername() {
        List<User> users = userService.findAllOrderByUsername();
        return ResponseMessage.success(users).toString();
    }
}
