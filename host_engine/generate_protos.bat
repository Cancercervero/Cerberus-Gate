@echo off
echo Generando archivos gRPC en Python desde orange.proto...
python -m grpc_tools.protoc -I..\proto --python_out=. --grpc_python_out=. ..\proto\orange.proto
echo Listo.
