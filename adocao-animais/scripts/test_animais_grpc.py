
import grpc

from proto import animais_pb2, animais_pb2_grpc


def main():
    with grpc.insecure_channel("localhost:50051") as channel:
        grpc.channel_ready_future(channel).result(timeout=5)

        client = animais_pb2_grpc.AnimalServiceStub(channel)

        animal = client.CreateAnimal(
            animais_pb2.CreateAnimalRequest(
                name="Rex",
                species="cachorro",
                breed="Vira-lata",
                age_years=3,
                description="Animal cadastrado para testar o sistema.",
            ),
            timeout=10,
        )

        print("Animal cadastrado:")
        print(animal.animal)

        resultado = client.ListAnimals(
            animais_pb2.ListAnimalsRequest(
                available_only=True
            ),
            timeout=10,
        )

        print("\nAnimais disponíveis no banco:")
        for item in resultado.animals:
            print(
                f"{item.id} | {item.name} | "
                f"{item.species} | disponível={item.available}"
            )


if __name__ == "__main__":
    main()
