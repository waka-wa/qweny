package com.example.qposrs;

import lombok.extern.slf4j.Slf4j;
import org.zeromq.SocketType;
import org.zeromq.ZContext;
import org.zeromq.ZMQ;

/**
 * Simple ZeroMQ publisher that sends strings on a TCP socket.
 *
 * The Python app subscribes to this socket to receive JSON arrays of objects.
 */
@Slf4j
public class ZmqPublisher implements AutoCloseable
{
    private final String address;
    private ZContext context;
    private ZMQ.Socket socket;

    public ZmqPublisher(String address)
    {
        this.address = address;
    }

    public void start()
    {
        context = new ZContext();
        socket = context.createSocket(SocketType.PUB);
        socket.bind(address);
        log.info("ZeroMQ publisher bound to {}", address);
    }

    public void publish(String message)
    {
        if (socket != null)
        {
            socket.send(message);
        }
    }

    @Override
    public void close()
    {
        if (socket != null)
        {
            socket.close();
        }
        if (context != null)
        {
            context.close();
        }
        log.info("ZeroMQ publisher closed");
    }
}