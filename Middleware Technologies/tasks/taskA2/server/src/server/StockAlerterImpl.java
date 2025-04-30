package server;

import gen.*;
import io.grpc.Status;
import io.grpc.stub.ServerCallStreamObserver;
import io.grpc.stub.StreamObserver;

import java.math.BigDecimal;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.protobuf.Timestamp;

import java.time.Instant;

public class StockAlerterImpl extends StockAlerterGrpc.StockAlerterImplBase {

    private static final Logger logger = Logger.getLogger(StockAlerterImpl.class.getName());

    // Key: subscriptionId
    private final ConcurrentHashMap<String, SubscriptionRequest> subscriptionDetails = new ConcurrentHashMap<>();

    // Key: subscriptionId
    private final ConcurrentHashMap<String, StreamObserver<NotificationMessage>> subscriberObservers = new ConcurrentHashMap<>();

    // Key: stockSymbol, Value: List of subscriptionIds
    private final ConcurrentHashMap<String, CopyOnWriteArrayList<String>> stockSubscriptions = new ConcurrentHashMap<>();

    private int compareMoney(Money m1, Money m2) {
        if (!m1.getCurrencyCode().equals(m2.getCurrencyCode())) {
            throw new IllegalArgumentException("Cannot compare money with different currency codes");
        }
        // Convert to BigDecimal for accurate comparison
        BigDecimal val1 = BigDecimal.valueOf(m1.getUnits()).add(BigDecimal.valueOf(m1.getNanos(), 9));
        BigDecimal val2 = BigDecimal.valueOf(m2.getUnits()).add(BigDecimal.valueOf(m2.getNanos(), 9));
        return val1.compareTo(val2);
    }

    private double moneyToDouble(Money money) {
        if (money == null) return 0.0;
        return money.getUnits() + money.getNanos() / 1_000_000_000.0;
    }

    private void removeSubscription(String subscriptionId) {
        logger.info("Removing subscription: " + subscriptionId);
        SubscriptionRequest details = subscriptionDetails.remove(subscriptionId);
        subscriberObservers.remove(subscriptionId);

        if (details != null) {
            String stockSymbol = details.getStockSymbol();
            CopyOnWriteArrayList<String> subs = stockSubscriptions.get(stockSymbol);
            if (subs != null) {
                subs.remove(subscriptionId);
                if (subs.isEmpty()) {
                    stockSubscriptions.remove(stockSymbol, subs);
                }
            }
        }
        logger.info("Subscription removed: " + subscriptionId);
    }

    @Override
    public void subscribe(SubscriptionRequest request, StreamObserver<NotificationMessage> responseObserver) {
        String subscriptionId = request.getSubscriptionId();
        String stockSymbol = request.getStockSymbol();

        if (subscriptionId.trim().isEmpty()) {
            logger.warning("Subscription attempt with empty subscription ID.");
            responseObserver.onError(Status.INVALID_ARGUMENT
                    .withDescription("Subscription ID cannot be empty.")
                    .asRuntimeException());
            return;
        }
        if (stockSymbol.trim().isEmpty()) {
            logger.warning("Subscription attempt with empty stock symbol. ID: " + subscriptionId);
            responseObserver.onError(Status.INVALID_ARGUMENT
                    .withDescription("Stock symbol cannot be empty.")
                    .asRuntimeException());
            return;
        }
        if (request.hasNotifyAbovePrice() && request.hasNotifyBelowPrice()) {
            if (compareMoney(request.getNotifyAbovePrice(), request.getNotifyBelowPrice()) > 0) {
                logger.warning("Subscription attempt where notifyAbovePrice < notifyBelowPrice. ID: " + subscriptionId);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("notify_above_price cannot be less than notify_below_price.")
                        .asRuntimeException());
                return;
            }
        }

        logger.info("Received subscription request: ID=" + subscriptionId + ", Symbol=" + stockSymbol
                + (request.hasNotifyAbovePrice() ? ", Above=" + request.getNotifyAbovePrice().getUnits() : "")
                + (request.hasNotifyBelowPrice() ? ", Below=" + request.getNotifyBelowPrice().getUnits() : ""));

        // 1. Store the full request details
        subscriptionDetails.put(subscriptionId, request);

        // 2. Store the observer for sending messages
        subscriberObservers.put(subscriptionId, responseObserver);

        // 3. Add to the stock symbol -> subscription ID mapping
        stockSubscriptions.computeIfAbsent(stockSymbol, k -> new CopyOnWriteArrayList<>()).add(subscriptionId);

        logger.info("Client subscribed: " + subscriptionId + " for " + stockSymbol);

        if (responseObserver instanceof ServerCallStreamObserver) {
            ((ServerCallStreamObserver<NotificationMessage>) responseObserver)
                    .setOnCancelHandler(() -> {
                        logger.warning("Client cancelled/disconnected: " + subscriptionId);
                        removeSubscription(subscriptionId);
                    });
        } else {
            logger.warning("Observer is not a ServerCallStreamObserver, cannot set cancellation handler for " + subscriptionId);
        }

        try {
            Timestamp timestamp = Timestamp.newBuilder().setSeconds(Instant.now().getEpochSecond()).build();
            NotificationMessage confirmation = NotificationMessage.newBuilder()
                    .setStockSymbol(stockSymbol)
                    .setAlertType(AlertType.GENERAL_UPDATE)
                    .setAlertMessage("Subscription confirmed for " + stockSymbol + " with ID: " + subscriptionId)
                    .setTimestamp(timestamp)
                    .build();
            responseObserver.onNext(confirmation);
            logger.info("Sent confirmation to " + subscriptionId);
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error sending confirmation to " + subscriptionId + ". Removing subscription.", e);
            removeSubscription(subscriptionId);
        }
    }

    @Override
    public void unsubscribe(UnsubscribeRequest request, StreamObserver<UnsubscribeResponse> responseObserver) {
        String subscriptionId = request.getSubscriptionId();
        if (subscriptionId.trim().isEmpty()) {
            logger.warning("Unsubscribe attempt with empty subscription ID.");
            responseObserver.onNext(UnsubscribeResponse.newBuilder()
                    .setConfirmationMessage("Error: Subscription ID cannot be empty.")
                    .build());
            responseObserver.onCompleted();
            return;
        }
        logger.info("Received unsubscribe request: ID=" + subscriptionId);

        StreamObserver<NotificationMessage> observer = subscriberObservers.get(subscriptionId);
        String message;

        if (observer != null) {
            removeSubscription(subscriptionId); // Remove from all maps
            message = "Successfully unsubscribed: " + subscriptionId;
            logger.info(message);
            try {
                observer.onCompleted();
            } catch (Exception e) {
                logger.log(Level.INFO, "Observer already closed or error during onCompleted for " + subscriptionId, e);
            }
        } else {
            message = "Subscription ID not found: " + subscriptionId;
            logger.warning(message);
        }

        // Send confirmation back to the client
        UnsubscribeResponse response = UnsubscribeResponse.newBuilder()
                .setConfirmationMessage(message)
                .build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    public void sendStockUpdate(NotificationMessage generalUpdate) {
        String stockSymbol = generalUpdate.getStockSymbol();
        Money currentPrice = generalUpdate.getCurrentPrice();
        Timestamp timestamp = generalUpdate.getTimestamp();

        CopyOnWriteArrayList<String> interestedSubscriptionIds = stockSubscriptions.get(stockSymbol);

        if (interestedSubscriptionIds == null || interestedSubscriptionIds.isEmpty()) {
            return; // No one is interested in this stock
        }

        for (String subId : interestedSubscriptionIds) {
            SubscriptionRequest subDetails = subscriptionDetails.get(subId);
            StreamObserver<NotificationMessage> observer = subscriberObservers.get(subId);

            if (subDetails == null || observer == null) {
                continue;
            }

            AlertType alertType = AlertType.GENERAL_UPDATE; // Default
            String alertMessage = String.format("Price update for %s: %.2f", stockSymbol, moneyToDouble(currentPrice));

            // 1. Check ABOVE threshold
            if (subDetails.hasNotifyAbovePrice() && compareMoney(currentPrice, subDetails.getNotifyAbovePrice()) > 0) {
                alertType = AlertType.PRICE_ABOVE_THRESHOLD;
                alertMessage = String.format("ALERT! %s price (%.2f) is ABOVE threshold (%.2f)",
                        stockSymbol, moneyToDouble(currentPrice), moneyToDouble(subDetails.getNotifyAbovePrice()));
                logger.info("Triggered ABOVE threshold for " + subId + " on " + stockSymbol);
            }
            // 2. Check BELOW threshold (only if ABOVE didn't trigger)
            else if (subDetails.hasNotifyBelowPrice() && compareMoney(currentPrice, subDetails.getNotifyBelowPrice()) < 0) {
                alertType = AlertType.PRICE_BELOW_THRESHOLD;
                alertMessage = String.format("ALERT! %s price (%.2f) is BELOW threshold (%.2f)",
                        stockSymbol, moneyToDouble(currentPrice), moneyToDouble(subDetails.getNotifyBelowPrice()));
                logger.info("Triggered BELOW threshold for " + subId + " on " + stockSymbol);
            }
            // 3. If no specific thresholds triggered, send a general update

            NotificationMessage specificNotification = NotificationMessage.newBuilder()
                    .setStockSymbol(stockSymbol)
                    .setCurrentPrice(currentPrice)
                    .setAlertType(alertType)
                    .setAlertMessage(alertMessage)
                    .addAllRelatedSymbols(generalUpdate.getRelatedSymbolsList()) // Copy related symbols
                    .setTimestamp(timestamp)
                    .build();
            try {
                observer.onNext(specificNotification);
            } catch (Exception e) {
                // Handle potential errors
                logger.log(Level.WARNING, "Error sending update to " + subId + ". Removing subscriber.", e);
                removeSubscription(subId);
            }
        }
    }
}