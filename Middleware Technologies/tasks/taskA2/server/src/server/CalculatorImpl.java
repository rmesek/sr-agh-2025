package server;

import gen.ArithmeticOpResult;
import gen.CalculatorGrpc.CalculatorImplBase;

public class CalculatorImpl extends CalculatorImplBase 
{
	@Override
	public void add(gen.ArithmeticOpArguments request,
			io.grpc.stub.StreamObserver<gen.ArithmeticOpResult> responseObserver) 
	{
		System.out.println("addRequest (" + request.getArg1() + ", " + request.getArg2() +")");
		int val = request.getArg1() + request.getArg2();
		ArithmeticOpResult result = ArithmeticOpResult.newBuilder().setRes(val).build();
		if(request.getArg1() > 100 && request.getArg2() > 100) try { Thread.sleep(5000); } catch(java.lang.InterruptedException ex) { }
		responseObserver.onNext(result);
		responseObserver.onCompleted();
	}

	@Override
	public void subtract(gen.ArithmeticOpArguments request,
			io.grpc.stub.StreamObserver<gen.ArithmeticOpResult> responseObserver) 
	{
		System.out.println("subtractRequest (" + request.getArg1() + ", " + request.getArg2() +")");
		int val = request.getArg1() - request.getArg2();
		ArithmeticOpResult result = ArithmeticOpResult.newBuilder().setRes(val).build();
		responseObserver.onNext(result);
		responseObserver.onCompleted();
	}


}
