package gen;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.71.0)",
    comments = "Source: stockalerter.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class StockAlerterGrpc {

  private StockAlerterGrpc() {}

  public static final java.lang.String SERVICE_NAME = "stockalerter.StockAlerter";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<gen.SubscriptionRequest,
      gen.NotificationMessage> getSubscribeMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Subscribe",
      requestType = gen.SubscriptionRequest.class,
      responseType = gen.NotificationMessage.class,
      methodType = io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
  public static io.grpc.MethodDescriptor<gen.SubscriptionRequest,
      gen.NotificationMessage> getSubscribeMethod() {
    io.grpc.MethodDescriptor<gen.SubscriptionRequest, gen.NotificationMessage> getSubscribeMethod;
    if ((getSubscribeMethod = StockAlerterGrpc.getSubscribeMethod) == null) {
      synchronized (StockAlerterGrpc.class) {
        if ((getSubscribeMethod = StockAlerterGrpc.getSubscribeMethod) == null) {
          StockAlerterGrpc.getSubscribeMethod = getSubscribeMethod =
              io.grpc.MethodDescriptor.<gen.SubscriptionRequest, gen.NotificationMessage>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Subscribe"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  gen.SubscriptionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  gen.NotificationMessage.getDefaultInstance()))
              .setSchemaDescriptor(new StockAlerterMethodDescriptorSupplier("Subscribe"))
              .build();
        }
      }
    }
    return getSubscribeMethod;
  }

  private static volatile io.grpc.MethodDescriptor<gen.UnsubscribeRequest,
      gen.UnsubscribeResponse> getUnsubscribeMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Unsubscribe",
      requestType = gen.UnsubscribeRequest.class,
      responseType = gen.UnsubscribeResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<gen.UnsubscribeRequest,
      gen.UnsubscribeResponse> getUnsubscribeMethod() {
    io.grpc.MethodDescriptor<gen.UnsubscribeRequest, gen.UnsubscribeResponse> getUnsubscribeMethod;
    if ((getUnsubscribeMethod = StockAlerterGrpc.getUnsubscribeMethod) == null) {
      synchronized (StockAlerterGrpc.class) {
        if ((getUnsubscribeMethod = StockAlerterGrpc.getUnsubscribeMethod) == null) {
          StockAlerterGrpc.getUnsubscribeMethod = getUnsubscribeMethod =
              io.grpc.MethodDescriptor.<gen.UnsubscribeRequest, gen.UnsubscribeResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Unsubscribe"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  gen.UnsubscribeRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  gen.UnsubscribeResponse.getDefaultInstance()))
              .setSchemaDescriptor(new StockAlerterMethodDescriptorSupplier("Unsubscribe"))
              .build();
        }
      }
    }
    return getUnsubscribeMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static StockAlerterStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<StockAlerterStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<StockAlerterStub>() {
        @java.lang.Override
        public StockAlerterStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new StockAlerterStub(channel, callOptions);
        }
      };
    return StockAlerterStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports all types of calls on the service
   */
  public static StockAlerterBlockingV2Stub newBlockingV2Stub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<StockAlerterBlockingV2Stub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<StockAlerterBlockingV2Stub>() {
        @java.lang.Override
        public StockAlerterBlockingV2Stub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new StockAlerterBlockingV2Stub(channel, callOptions);
        }
      };
    return StockAlerterBlockingV2Stub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static StockAlerterBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<StockAlerterBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<StockAlerterBlockingStub>() {
        @java.lang.Override
        public StockAlerterBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new StockAlerterBlockingStub(channel, callOptions);
        }
      };
    return StockAlerterBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static StockAlerterFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<StockAlerterFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<StockAlerterFutureStub>() {
        @java.lang.Override
        public StockAlerterFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new StockAlerterFutureStub(channel, callOptions);
        }
      };
    return StockAlerterFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void subscribe(gen.SubscriptionRequest request,
        io.grpc.stub.StreamObserver<gen.NotificationMessage> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getSubscribeMethod(), responseObserver);
    }

    /**
     */
    default void unsubscribe(gen.UnsubscribeRequest request,
        io.grpc.stub.StreamObserver<gen.UnsubscribeResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUnsubscribeMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service StockAlerter.
   */
  public static abstract class StockAlerterImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return StockAlerterGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service StockAlerter.
   */
  public static final class StockAlerterStub
      extends io.grpc.stub.AbstractAsyncStub<StockAlerterStub> {
    private StockAlerterStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected StockAlerterStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new StockAlerterStub(channel, callOptions);
    }

    /**
     */
    public void subscribe(gen.SubscriptionRequest request,
        io.grpc.stub.StreamObserver<gen.NotificationMessage> responseObserver) {
      io.grpc.stub.ClientCalls.asyncServerStreamingCall(
          getChannel().newCall(getSubscribeMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void unsubscribe(gen.UnsubscribeRequest request,
        io.grpc.stub.StreamObserver<gen.UnsubscribeResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUnsubscribeMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service StockAlerter.
   */
  public static final class StockAlerterBlockingV2Stub
      extends io.grpc.stub.AbstractBlockingStub<StockAlerterBlockingV2Stub> {
    private StockAlerterBlockingV2Stub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected StockAlerterBlockingV2Stub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new StockAlerterBlockingV2Stub(channel, callOptions);
    }

    /**
     */
    @io.grpc.ExperimentalApi("https://github.com/grpc/grpc-java/issues/10918")
    public io.grpc.stub.BlockingClientCall<?, gen.NotificationMessage>
        subscribe(gen.SubscriptionRequest request) {
      return io.grpc.stub.ClientCalls.blockingV2ServerStreamingCall(
          getChannel(), getSubscribeMethod(), getCallOptions(), request);
    }

    /**
     */
    public gen.UnsubscribeResponse unsubscribe(gen.UnsubscribeRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUnsubscribeMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do limited synchronous rpc calls to service StockAlerter.
   */
  public static final class StockAlerterBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<StockAlerterBlockingStub> {
    private StockAlerterBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected StockAlerterBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new StockAlerterBlockingStub(channel, callOptions);
    }

    /**
     */
    public java.util.Iterator<gen.NotificationMessage> subscribe(
        gen.SubscriptionRequest request) {
      return io.grpc.stub.ClientCalls.blockingServerStreamingCall(
          getChannel(), getSubscribeMethod(), getCallOptions(), request);
    }

    /**
     */
    public gen.UnsubscribeResponse unsubscribe(gen.UnsubscribeRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUnsubscribeMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service StockAlerter.
   */
  public static final class StockAlerterFutureStub
      extends io.grpc.stub.AbstractFutureStub<StockAlerterFutureStub> {
    private StockAlerterFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected StockAlerterFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new StockAlerterFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<gen.UnsubscribeResponse> unsubscribe(
        gen.UnsubscribeRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUnsubscribeMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_SUBSCRIBE = 0;
  private static final int METHODID_UNSUBSCRIBE = 1;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_SUBSCRIBE:
          serviceImpl.subscribe((gen.SubscriptionRequest) request,
              (io.grpc.stub.StreamObserver<gen.NotificationMessage>) responseObserver);
          break;
        case METHODID_UNSUBSCRIBE:
          serviceImpl.unsubscribe((gen.UnsubscribeRequest) request,
              (io.grpc.stub.StreamObserver<gen.UnsubscribeResponse>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getSubscribeMethod(),
          io.grpc.stub.ServerCalls.asyncServerStreamingCall(
            new MethodHandlers<
              gen.SubscriptionRequest,
              gen.NotificationMessage>(
                service, METHODID_SUBSCRIBE)))
        .addMethod(
          getUnsubscribeMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              gen.UnsubscribeRequest,
              gen.UnsubscribeResponse>(
                service, METHODID_UNSUBSCRIBE)))
        .build();
  }

  private static abstract class StockAlerterBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    StockAlerterBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return gen.StockAlerterProto.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("StockAlerter");
    }
  }

  private static final class StockAlerterFileDescriptorSupplier
      extends StockAlerterBaseDescriptorSupplier {
    StockAlerterFileDescriptorSupplier() {}
  }

  private static final class StockAlerterMethodDescriptorSupplier
      extends StockAlerterBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    StockAlerterMethodDescriptorSupplier(java.lang.String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (StockAlerterGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new StockAlerterFileDescriptorSupplier())
              .addMethod(getSubscribeMethod())
              .addMethod(getUnsubscribeMethod())
              .build();
        }
      }
    }
    return result;
  }
}
