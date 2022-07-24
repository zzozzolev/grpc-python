"""The Python implementation of the GRPC helloworld.Greeter server."""

from concurrent import futures
import logging
from typing import Iterable

import grpc
from google.protobuf import any_pb2
from google.rpc import error_details_pb2, code_pb2, status_pb2
from grpc_reflection.v1alpha import reflection
from grpc_status import rpc_status
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
import helloworld_pb2, helloworld_pb2_grpc


class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(
        self, continuation, handler_call_details: grpc.HandlerCallDetails
    ):
        print(f"----------- Before {handler_call_details.method} -----------")
        result = continuation(handler_call_details)
        print(f"----------- After {handler_call_details.method} -----------")
        return result


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    STREAM_GREETING = ["one", "two", "three", "four"]

    def SayHello(
        self, request: helloworld_pb2.HelloRequest, context: grpc.ServicerContext
    ):
        if request.name == "anonymous":
            status = self._get_anonymous_status()
            context.abort_with_status(rpc_status.to_status(status))

        is_welcome = True if request.name == "hyemi" else False

        # metadata
        print("metadata")
        for key, value in context.invocation_metadata():
            print(key, value)

        context.set_trailing_metadata((("retry", "false"),))

        return helloworld_pb2.HelloReply(
            message=f"Hello, {request.name}!", is_welcome=is_welcome
        )

    def SayHelloStream(
        self, request: helloworld_pb2.HelloRequest, context: grpc.ServicerContext
    ) -> Iterable[helloworld_pb2.HelloReply]:
        is_welcome = True if request.name == "hyemi" else False
        for greeting in self.STREAM_GREETING:
            yield helloworld_pb2.HelloReply(message=greeting, is_welcome=is_welcome)

    def SayHelloClientStream(
        self,
        request_iterator: Iterable[helloworld_pb2.HelloRequest],
        context: grpc.ServicerContext,
    ) -> helloworld_pb2.HelloReply:
        names = ", ".join([request.name for request in request_iterator])
        return helloworld_pb2.HelloReply(
            message=f"Hello everyone!, {names}", is_welcome=True
        )

    def _get_anonymous_status(self):
        detail = any_pb2.Any()
        detail.Pack(
            error_details_pb2.BadRequest(
                field_violations=[
                    error_details_pb2.BadRequest.FieldViolation(
                        field="name", description="name 'anonymous' is invalid."
                    )
                ]
            )
        )
        return status_pb2.Status(
            code=code_pb2.INVALID_ARGUMENT,
            message="Bad Request",
            details=[detail],
        )


def serve():
    logging_interceptor = LoggingInterceptor()
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), interceptors=[logging_interceptor]
    )

    # greeter service
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)

    # health check service
    health_check_servicer = health.HealthServicer()
    health_check_servicer._server_status[
        "Greeter"
    ] = health_pb2.HealthCheckResponse.ServingStatus.SERVING
    health_pb2_grpc.add_HealthServicer_to_server(health_check_servicer, server)

    # reflection
    SERVICE_NAMES = (
        helloworld_pb2.DESCRIPTOR.services_by_name["Greeter"].full_name,
        health_pb2.DESCRIPTOR.services_by_name["Health"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server=server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
