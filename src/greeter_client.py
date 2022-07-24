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
        stub = health_pb2_grpc.HealthStub(channel)
        response = stub.Check(health_pb2.HealthCheckRequest(service="Greeter"))
        print("----------- Health Check -----------")
        print(response)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        response = stub.SayHello(
            helloworld_pb2.HelloRequest(
                name="damian", age=32, gender=helloworld_pb2.MALE
            )
        )
        print_response(response, "Unary-Unary")

        try:
            response = stub.SayHello(helloworld_pb2.HelloRequest(name="anonymous"))
        except grpc.RpcError as rpc_error:
            print("!!! rpc failed !!!")
            status = rpc_status.from_call(rpc_error)
            for detail in status.details:
                if detail.Is(error_details_pb2.BadRequest.DESCRIPTOR):
                    info = error_details_pb2.BadRequest()
                    detail.Unpack(info)
                    print(info)
                else:
                    print("Unexpected error")

        stream = stub.SayHelloStream(
            helloworld_pb2.HelloRequest(
                name="hyemi", age=10, gender=helloworld_pb2.FEMALE
            )
        )

        for response in stream:
            print_response(response, "Unary-Streaming")


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
