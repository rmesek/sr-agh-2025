import pika


class RabbitMQConnection:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost")
        )
        self.channel = self.connection.channel()
        self.setup_exchanges_and_queues()

    def setup_exchanges_and_queues(self):
        self.channel.exchange_declare(
            exchange="orders_exchange",
            exchange_type="direct",
            durable=True,
        )

        self.channel.exchange_declare(
            exchange="confirmations_exchange",
            exchange_type="direct",
            durable=True,
        )

        self.channel.exchange_declare(
            exchange="admin_broadcast",
            exchange_type="fanout",
            durable=True,
        )
        self.channel.exchange_declare(
            exchange="admin_to_teams",
            exchange_type="fanout",
            durable=True,
        )
        self.channel.exchange_declare(
            exchange="admin_to_suppliers",
            exchange_type="fanout",
            durable=True,
        )

        self.channel.exchange_declare(
            exchange="admin_copy",
            exchange_type="fanout",
            durable=True,
        )

    def close(self):
        self.connection.close()


def setup_rabbitmq():
    connection = RabbitMQConnection()
    connection.close()
