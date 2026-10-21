
import grpc

from proto import adocao_pb2, adocao_pb2_grpc
from proto import animais_pb2, animais_pb2_grpc


def main():
    # Buscar um animal real cadastrado no Supabase.
    with grpc.insecure_channel("localhost:50051") as channel:
        grpc.channel_ready_future(channel).result(timeout=5)

        animal_client = animais_pb2_grpc.AnimalServiceStub(channel)

        resultado = animal_client.ListAnimals(
            animais_pb2.ListAnimalsRequest(available_only=True),
            timeout=10,
        )

        if not resultado.animals:
            print("Nenhum animal disponível. Cadastre um animal primeiro.")
            return

        animal = resultado.animals[0]
        print(f"Animal selecionado: {animal.name} ({animal.id})")

    # Criar a solicitação por meio do segundo microsserviço.
    with grpc.insecure_channel("localhost:50052") as channel:
        grpc.channel_ready_future(channel).result(timeout=5)

        adoption_client = adocao_pb2_grpc.AdocaoServiceStub(channel)

        resposta = adoption_client.CreateAdoption(
            adocao_pb2.CreateAdoptionRequest(
                animal_id=animal.id,
                adopter_name="Maria Silva",
                adopter_email="maria@example.com",
            ),
            timeout=10,
        )

        print("\nSolicitação criada:")
        print(resposta.adoption)

        lista = adoption_client.ListAdoptions(
            adocao_pb2.ListAdoptionsRequest(),
            timeout=10,
        )

        print(f"\nTotal de solicitações encontradas: {len(lista.adoptions)}")


if __name__ == "__main__":
    main()
