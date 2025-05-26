import com.rabbitmq.client.*;

import java.io.IOException;

public class Z1ab_Consumer {

    public static void main(String[] argv) throws Exception {

        // info
        System.out.println("Z1b CONSUMER");

        // connection & channel
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        Connection connection = factory.newConnection();
        Channel channel = connection.createChannel();

        // queue
        String QUEUE_NAME = "queue1";
        channel.queueDeclare(QUEUE_NAME, false, false, false, null);
        channel.basicQos(1);

        boolean autoAck = true;

        // consumer (handle msg)
        Consumer consumer = new DefaultConsumer(channel) {
            @Override
            public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) throws IOException {
                String message = new String(body, "UTF-8");
                System.out.println("Received: " + message);

                try {
                    int timeToSleep = Integer.parseInt(message);
                    System.out.println("Processing message for " + timeToSleep + " seconds...");
                    Thread.sleep(timeToSleep * 1000);
                    System.out.println("Processing complete for: " + message);

                    if (!autoAck) {
                        channel.basicAck(envelope.getDeliveryTag(), false);
                        System.out.println("Message acknowledged: " + message);
                    }
                } catch (InterruptedException e) {
                    e.printStackTrace();
                } catch (NumberFormatException e) {
                    System.out.println("Invalid message format. Expected a number.");
                    if (!autoAck) {
                        channel.basicAck(envelope.getDeliveryTag(), false);
                    }
                }
            }
        };

        // start listening
        System.out.println("Waiting for messages... (autoAck = " + autoAck + ")");
        channel.basicConsume(QUEUE_NAME, autoAck, consumer);

        // close
        // channel.close();
        // connection.close();
    }
}
