package com.backend.be.pojo;

public class ResponseMessage<T> {
    private String message;
    private T data;
    private Integer code;

    public ResponseMessage(Integer code,String message, T data) {
        this.message = message;
        this.data = data;
        this.code = code;
    }
    public String getMessage() {
        return message;
    }   
    public Object getData() {
        return data;
    }
    public void setMessage(String message) {
        this.message = message;
    }
    public static <T> ResponseMessage success( T data) {
        return new ResponseMessage(200, "Success", data);
    }
    public static <T> ResponseMessage error( T data) {
        return new ResponseMessage(500, "Error", data);
    }
    @Override
    public String toString() {
        // TODO Auto-generated method stub
        return "ResponseMessage [message=" + message + ", data=" + data + ", code=" + code + "]";
    }
}
