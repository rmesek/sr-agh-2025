package server;

import io.grpc.Server;
import io.grpc.ServerBuilder;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.logging.*;

public class StockAlerterServer {

    private static final Logger logger = Logger.getLogger(StockAlerterServer.class.getName());
    private Server server;
    private final int port;
    private final StockAlerterImpl serviceImpl;

    public StockAlerterServer(int port) {
        this.port = port;
        this.serviceImpl = new StockAlerterImpl();
    }

    public void start() throws IOException {
        server = ServerBuilder.forPort(port)
                .addService(serviceImpl)
                .permitKeepAliveTime(5000, TimeUnit.MILLISECONDS)
                .permitKeepAliveWithoutCalls(true)
                .build()
                .start();
        logger.info("Server started, listening on " + port);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.err.println("*** Shutting down gRPC server since JVM is shutting down");
            try {
                StockAlerterServer.this.stop();
            } catch (InterruptedException e) {
                e.printStackTrace(System.err);
                Thread.currentThread().interrupt();
            }
            System.err.println("*** Server shut down");
        }));

        startStockMonitor(); // Start the simulator
    }

    public void stop() throws InterruptedException {
        if (server != null) {
            server.shutdown().awaitTermination(30, TimeUnit.SECONDS);
        }
    }

    private void blockUntilShutdown() throws InterruptedException {
        if (server != null) {
            server.awaitTermination();
        }
    }

    private void startStockMonitor() {
        StockMonitorSimulator simulator = new StockMonitorSimulator(
                this.serviceImpl,
                "AAPL",
                175.50,
                10.5,
                List.of("GOOG", "MSFT"),
                5000
        );
        simulator.start();

        StockMonitorSimulator simulator2 = new StockMonitorSimulator(
                this.serviceImpl,
                "TSLA",
                900.0,
                5.0,
                List.of("F", "GM"),
                7000
        );
        simulator2.start();

        StockMonitorSimulator simulator3 = new StockMonitorSimulator(
                this.serviceImpl,
                "AMZN",
                330.0,
                10.0,
                List.of("WMT", "COST"),
                10000
        );
        simulator3.start();

        logger.info("Stock monitor simulator initiated.");
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        int port = 50051;
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);  // Command line argument for port
            } catch (NumberFormatException e) {
                System.err.println("Invalid port number: " + args[0] + ". Using default " + port);
            }
        }

        final StockAlerterServer server = new StockAlerterServer(port);
        server.start();
        server.blockUntilShutdown();
    }
}