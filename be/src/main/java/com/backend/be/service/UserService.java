package com.backend.be.service;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.backend.be.pojo.User;
import com.backend.be.repository.UserRepository;

@Service
public class UserService implements IUserService{

    @Autowired
    UserRepository userRepository;
    
    @Override
    public User createUser(User user) {
        User proj = new User();
        BeanUtils.copyProperties(user, proj);
        userRepository.save(proj);
        System.out.println("User created: " + user.getUsername());
        return proj;
    }
    
    @Override
    public Optional<User> findByUsername(String username) {
        return userRepository.findByUsername(username);
    }
    
    @Override
    public List<User> findByUsernameContaining(String username) {
        return userRepository.findByUsernameContaining(username);
    }
    
    @Override
    public boolean existsByUsername(String username) {
        return userRepository.existsByUsername(username);
    }
    
    @Override
    public Optional<User> findByUsernameAndPassword(String username, String password) {
        return userRepository.findByUsernameAndPassword(username, password);
    }
    
    @Override
    public List<User> findAll() {
        return userRepository.findAll();
    }
    
    @Override
    public Optional<User> findById(Integer id) {
        return userRepository.findById(id);
    }
    
    @Override
    public User updateUser(User user) {
        if (user.getId() == null || !userRepository.existsById(user.getId())) {
            throw new RuntimeException("用户不存在，无法更新");
        }
        return userRepository.save(user);
    }
    
    @Override
    public void deleteUser(Integer id) {
        if (!userRepository.existsById(id)) {
            throw new RuntimeException("用户不存在，无法删除");
        }
        userRepository.deleteById(id);
    }
    
    @Override
    public long countUsers() {
        return userRepository.countAllUsers();
    }
    
    @Override
    public List<User> findAllOrderByUsername() {
        return userRepository.findAllOrderByUsername();
    }

}
