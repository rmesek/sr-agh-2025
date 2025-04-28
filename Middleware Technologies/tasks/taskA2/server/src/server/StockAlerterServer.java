package server;

import io.grpc.Server;
import io.grpc.ServerBuilder;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

public class StockAlerterServer {

    private static final Logger logger = Logger.getLogger(StockAlerterServer.class.getName());
    private Server server;
    private final int port;
    private final StockAlerterImpl serviceImpl; // Instance of our service implementation

    public StockAlerterServer(int port) {
        this.port = port;
        this.serviceImpl = new StockAlerterImpl(); // Create the service implementation
    }

    public void start() throws IOException {
        server = ServerBuilder.forPort(port)
                .addService(serviceImpl) // Register the service implementation
                .build()
                .start();
        logger.info("Server started, listening on " + port);

        // Add shutdown hook
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

        // Start the *configurable* stock monitor simulator
        startStockMonitor(); // Call the method to start the simulator
    }

    public void stop() throws InterruptedException {
        if (server != null) {
            // Consider adding logic here to signal the simulator thread to stop if needed
            server.shutdown().awaitTermination(30, TimeUnit.SECONDS);
        }
    }

    /**
     * Await termination on the main thread since the grpc library uses daemon threads.
     */
    private void blockUntilShutdown() throws InterruptedException {
        if (server != null) {
            server.awaitTermination();
        }
    }

    // Method to configure and start the simulator
    private void startStockMonitor() {
        // Create and start the simulator instance
        StockMonitorSimulator simulator = new StockMonitorSimulator(
                this.serviceImpl,
                "AAPL",
                175.50,
                1.50,
                List.of("GOOG", "MSFT"),
                5000
        );
        simulator.start(); // Start it in its own thread

        // You could start multiple simulators for different stocks here if needed
        StockMonitorSimulator simulator2 = new StockMonitorSimulator(
                this.serviceImpl,
                "TSLA",
                900.0,
                5.0,
                List.of("F", "GM"),
                7000
        );
        simulator2.start();

        logger.info("Stock monitor simulator initiated.");
    }


    public static void main(String[] args) throws IOException, InterruptedException {
        // Set a default port or get from command line args
        int port = 50051;
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException e) {
                System.err.println("Invalid port number: " + args[0] + ". Using default " + port);
            }
        }

        final StockAlerterServer server = new StockAlerterServer(port);
        server.start();
        server.blockUntilShutdown();
    }
}