"""The Python implementation of the GRPC helloworld.Greeter server."""

from concurrent import futures
import logging
from typing import Iterable

import grpc
from google.protobuf import any_pb2
from google.rpc import error_details_pb2, code_pb2, status_pb2
from grpc_reflection.v1alpha import reflection
from grpc_status import rpc_status
import helloworld_pb2, helloworld_pb2_grpc


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    STREAM_GREETING = ["one", "two", "three", "four"]

    def SayHello(
        self, request: helloworld_pb2.HelloRequest, context: grpc.ServicerContext
    ):
        if request.name == "anonymous":
            status = self._get_anonymous_status()
            context.abort_with_status(rpc_status.to_status(status))

        is_welcome = True if request.name == "hyemi" else False
        return helloworld_pb2.HelloReply(
            message=f"Hello, {request.name}!", is_welcome=is_welcome
        )

    def SayHelloStream(
        self, request: helloworld_pb2.HelloRequest, context: grpc.ServicerContext
    ) -> Iterable[helloworld_pb2.HelloReply]:
        is_welcome = True if request.name == "hyemi" else False
        for greeting in self.STREAM_GREETING:
            yield helloworld_pb2.HelloReply(message=greeting, is_welcome=is_welcome)

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
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    SERVICE_NAMES = (
        helloworld_pb2.DESCRIPTOR.services_by_name["Greeter"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server=server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
