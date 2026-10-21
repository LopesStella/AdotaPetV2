
from concurrent import futures

import grpc
from sqlalchemy import select, update

from microsservicos.animais.database import Base, SessionLocal, engine
from microsservicos.animais.models import Animal
from proto import animais_pb2, animais_pb2_grpc


def to_proto(animal):
    return animais_pb2.Animal(
        id=animal.id,
        name=animal.name,
        species=animal.species,
        breed=animal.breed,
        age_years=animal.age_years,
        description=animal.description,
        available=animal.available,
    )


class AnimalService(animais_pb2_grpc.AnimalServiceServicer):

    def CreateAnimal(self, request, context):
        name = request.name.strip()
        species = request.species.strip().lower()
        breed = request.breed.strip()
        description = request.description.strip()

        if not name or not species or not breed or not description:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Nome, espécie, raça e descrição são obrigatórios.",
            )

        if species not in ("cachorro", "gato"):
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "A espécie deve ser cachorro ou gato.",
            )

        if request.age_years < 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "A idade não pode ser negativa.",
            )

        with SessionLocal() as db:
            animal = Animal(
                name=name,
                species=species,
                breed=breed,
                age_years=request.age_years,
                description=description,
                available=True,
            )

            db.add(animal)
            db.commit()
            db.refresh(animal)

            return animais_pb2.AnimalResponse(
                animal=to_proto(animal)
            )

    def GetAnimal(self, request, context):
        with SessionLocal() as db:
            animal = db.get(Animal, request.id)

            if animal is None:
                context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    "Animal não encontrado.",
                )

            return animais_pb2.AnimalResponse(
                animal=to_proto(animal)
            )

    def ListAnimals(self, request, context):
        with SessionLocal() as db:
            query = select(Animal).order_by(Animal.name)

            if request.available_only:
                query = query.where(Animal.available.is_(True))

            animals = db.scalars(query).all()

            return animais_pb2.ListAnimalsResponse(
                animals=[to_proto(animal) for animal in animals]
            )

    def UpdateAnimal(self, request, context):
        name = request.name.strip()
        species = request.species.strip().lower()
        breed = request.breed.strip()
        description = request.description.strip()

        if not name or not breed or not description:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Nome, raça e descrição são obrigatórios.",
            )

        if species not in ("cachorro", "gato"):
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "A espécie deve ser cachorro ou gato.",
            )

        if request.age_years < 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "A idade não pode ser negativa.",
            )

        with SessionLocal() as db:
            animal = db.scalar(
                select(Animal)
                .where(Animal.id == request.id)
                .with_for_update()
            )

            if animal is None:
                context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    "Animal não encontrado.",
                )

            if animal.reservation_adoption_id is not None:
                context.abort(
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "Animal reservado por uma adoção aprovada.",
                )

            animal.name = name
            animal.species = species
            animal.breed = breed
            animal.age_years = request.age_years
            animal.description = description
            animal.available = request.available

            db.commit()
            db.refresh(animal)

            return animais_pb2.AnimalResponse(
                animal=to_proto(animal)
            )

    def ReserveAnimal(self, request, context):
        animal_id = request.animal_id.strip()
        adoption_id = request.adoption_id.strip()

        if not animal_id or not adoption_id:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Animal e adoção são obrigatórios.",
            )

        with SessionLocal() as db:
            # Reserva atômica: apenas uma adoção consegue
            # alterar o animal de disponível para indisponível.
            result = db.execute(
                update(Animal)
                .where(
                    Animal.id == animal_id,
                    Animal.available.is_(True),
                    Animal.reservation_adoption_id.is_(None),
                )
                .values(
                    available=False,
                    reservation_adoption_id=adoption_id,
                )
            )

            if result.rowcount == 1:
                db.commit()

                return animais_pb2.ReserveAnimalResponse(
                    newly_reserved=True
                )

            # Se a mesma adoção já reservou o animal,
            # a operação pode ser repetida com segurança.
            animal = db.get(Animal, animal_id)

            if animal is None:
                context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    "Animal não encontrado.",
                )

            if animal.reservation_adoption_id == adoption_id:
                return animais_pb2.ReserveAnimalResponse(
                    newly_reserved=False
                )

            context.abort(
                grpc.StatusCode.FAILED_PRECONDITION,
                "Animal indisponível ou reservado por outra adoção.",
            )

    def ReleaseAnimal(self, request, context):
        animal_id = request.animal_id.strip()
        adoption_id = request.adoption_id.strip()

        if not animal_id or not adoption_id:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Animal e adoção são obrigatórios.",
            )

        with SessionLocal() as db:
            # Libera somente se a reserva pertence
            # à adoção informada.
            result = db.execute(
                update(Animal)
                .where(
                    Animal.id == animal_id,
                    Animal.reservation_adoption_id == adoption_id,
                )
                .values(
                    available=True,
                    reservation_adoption_id=None,
                )
            )

            db.commit()

            return animais_pb2.ReleaseAnimalResponse(
                released=result.rowcount == 1
            )


def serve():
    Base.metadata.create_all(bind=engine)

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    animais_pb2_grpc.add_AnimalServiceServicer_to_server(
        AnimalService(),
        server,
    )

    server.add_insecure_port("[::]:50051")
    server.start()

    print("Microsserviço de Animais iniciado na porta 50051.")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()
