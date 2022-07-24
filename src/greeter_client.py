# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python implementation of the GRPC helloworld.Greeter client."""

import logging

import grpc
from google.rpc import error_details_pb2
from grpc_status import rpc_status
from grpc_health.v1 import health_pb2_grpc, health_pb2
import helloworld_pb2
import helloworld_pb2_grpc


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        # health check
        stub = health_pb2_grpc.HealthStub(channel)
        response = stub.Check(health_pb2.HealthCheckRequest(service="Greeter"))
        print("----------- Health Check -----------")
        print(response)

        # Unary-Unary call (metadata)
        stub = helloworld_pb2_grpc.GreeterStub(channel)
        response, call = stub.SayHello.with_call(
            helloworld_pb2.HelloRequest(
                name="damian", age=32, gender=helloworld_pb2.MALE
            ),
            metadata=((("access-token", "fake_token"),)),
        )
        print_response(response, "Unary-Unary")
        print("- - - - - -")
        print("metadata")
        for key, value in call.trailing_metadata():
            print(key, value)

        # error handling
        try:
            response = stub.SayHello(helloworld_pb2.HelloRequest(name="anonymous"))
        except grpc.RpcError as rpc_error:
            print("----------- rpc failed -----------")
            status = rpc_status.from_call(rpc_error)
            for detail in status.details:
                if detail.Is(error_details_pb2.BadRequest.DESCRIPTOR):
                    info = error_details_pb2.BadRequest()
                    detail.Unpack(info)
                    print(info)
                else:
                    print("Unexpected error")

        # Unary-Stream call
        stream = stub.SayHelloStream(
            helloworld_pb2.HelloRequest(
                name="hyemi", age=10, gender=helloworld_pb2.FEMALE
            )
        )
        for response in stream:
            print_response(response, "Unary-Streaming")

        # Stream-Unary call
        hello_requests = iter(
            [
                helloworld_pb2.HelloRequest(
                    name="jam", age=1, gender=helloworld_pb2.FEMALE
                ),
                helloworld_pb2.HelloRequest(
                    name="ham", age=2, gender=helloworld_pb2.FEMALE
                ),
                helloworld_pb2.HelloRequest(
                    name="tam", age=3, gender=helloworld_pb2.MALE
                ),
            ]
        )
        response = stub.SayHelloClientStream(hello_requests)
        print_response(response, "Streaming-Unary")

        # Stream-Stream call
        hello_requests = iter(
            [
                helloworld_pb2.HelloRequest(
                    name="jam1", age=1, gender=helloworld_pb2.FEMALE
                ),
                helloworld_pb2.HelloRequest(
                    name="jam2", age=2, gender=helloworld_pb2.FEMALE
                ),
                helloworld_pb2.HelloRequest(
                    name="jam3", age=3, gender=helloworld_pb2.MALE
                ),
            ]
        )
        stream = stub.SayHelloBiStream(hello_requests)
        for response in stream:
            print_response(response, "Streaming-Streaming")


def print_response(response, rpc_life_cycle):
    print(f"----------- {rpc_life_cycle} -----------")
    print("response")
    print(str(response))
    print("- - - - - -")
    print("fields")
    print("message: " + response.message)
    print("is_welcome: " + str(response.is_welcome))


if __name__ == "__main__":
    logging.basicConfig()
    run()
