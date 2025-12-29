package com.backend.be.repository;

import org.springframework.data.repository.CrudRepository;

import com.backend.be.pojo.User;
public interface IUserRepository extends CrudRepository<User, Integer> {


    <S extends User> S save(S user);
    
}
