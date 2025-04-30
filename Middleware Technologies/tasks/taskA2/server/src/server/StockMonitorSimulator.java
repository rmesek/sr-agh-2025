package server;

import gen.*;
import com.google.protobuf.Timestamp;

import java.time.Instant;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

public class StockMonitorSimulator implements Runnable {

    private static final Logger logger = Logger.getLogger(StockMonitorSimulator.class.getName());

    private final StockAlerterImpl service;
    private final String stockSymbol;
    private final List<String> relatedSymbols;
    private final long updateIntervalMillis;
    private final double fluctuationAmount;
    private double currentPrice;


    public StockMonitorSimulator(StockAlerterImpl service,
                                 String stockSymbol,
                                 double startingPrice,
                                 double fluctuationAmount,
                                 List<String> relatedSymbols,
                                 long updateIntervalMillis) {

        if (service == null) {
            throw new IllegalArgumentException("StockAlerterImpl service cannot be null");
        }
        if (stockSymbol == null || stockSymbol.isEmpty()) {
            throw new IllegalArgumentException("Stock symbol cannot be null or empty");
        }
        if (updateIntervalMillis <= 0) {
            throw new IllegalArgumentException("Update interval must be positive");
        }
        if (fluctuationAmount < 0) {
            throw new IllegalArgumentException("Fluctuation amount cannot be negative");
        }

        this.service = service;
        this.stockSymbol = stockSymbol;
        this.currentPrice = startingPrice;
        this.fluctuationAmount = fluctuationAmount;
        this.relatedSymbols = relatedSymbols != null ? relatedSymbols : List.of();
        this.updateIntervalMillis = updateIntervalMillis;

        logger.info(String.format("Initialized StockMonitorSimulator for %s: startPrice=%.2f, fluctuation=%.2f, interval=%dms",
                stockSymbol, startingPrice, fluctuationAmount, updateIntervalMillis));
    }

    @Override
    public void run() {
        logger.info("Stock monitor simulator thread started for " + stockSymbol);
        while (!Thread.currentThread().isInterrupted()) {
            try {
                Thread.sleep(updateIntervalMillis);

                // Random value between -fluctuationAmount and +fluctuationAmount
                double change = (Math.random() * 2 - 1) * fluctuationAmount;
                currentPrice += change;

                Money priceMoney = Money.newBuilder()
                        .setCurrencyCode("USD")
                        .setUnits((long) currentPrice)
                        .setNanos((int) ((currentPrice - Math.floor(currentPrice)) * 1_000_000_000))
                        .build();

                Timestamp timestamp = Timestamp.newBuilder().setSeconds(Instant.now().getEpochSecond()).build();

                NotificationMessage.Builder notificationBuilder = NotificationMessage.newBuilder()
                        .setStockSymbol(stockSymbol)
                        .setCurrentPrice(priceMoney)
                        .setAlertType(AlertType.GENERAL_UPDATE)
                        .setAlertMessage(String.format("Price update for %s: %.2f", stockSymbol, currentPrice))
                        .setTimestamp(timestamp);

                if (!relatedSymbols.isEmpty()) {
                    notificationBuilder.addAllRelatedSymbols(relatedSymbols);
                }

                NotificationMessage notification = notificationBuilder.build();

                logger.fine("Simulator [" + stockSymbol + "] generated update: " + notification.getAlertMessage());

                service.sendStockUpdate(notification); // Send the update to all subscribers

            } catch (InterruptedException e) {
                logger.info("Stock monitor simulator thread interrupted for " + stockSymbol);
                Thread.currentThread().interrupt();
            } catch (Exception e) {
                logger.log(Level.SEVERE, "Error in stock monitor simulator loop for " + stockSymbol, e);
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                }
            }
        }
        logger.info("Stock monitor simulator thread finished for " + stockSymbol);
    }

    public void start() {
        Thread simulatorThread = new Thread(this);
        simulatorThread.setName("StockMonitor-" + stockSymbol);
        simulatorThread.setDaemon(true);
        simulatorThread.start();
    }
}