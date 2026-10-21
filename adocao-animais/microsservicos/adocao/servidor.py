
from concurrent import futures

import grpc
from sqlalchemy import select

from microsservicos.adocao.database import Base, SessionLocal, engine
from microsservicos.adocao.models import Adoption
from proto import animais_pb2, animais_pb2_grpc
from proto import adocao_pb2, adocao_pb2_grpc


ANIMAL_SERVICE_ADDRESS = "localhost:50051"

VALID_STATUSES = {"pendente", "aprovada", "rejeitada"}


def to_proto(adoption):
    return adocao_pb2.Adoption(
        id=adoption.id,
        animal_id=adoption.animal_id,
        adopter_name=adoption.adopter_name,
        adopter_email=adoption.adopter_email,
        status=adoption.status,
        created_at=adoption.created_at.isoformat(),
    )


class AdocaoService(adocao_pb2_grpc.AdocaoServiceServicer):

    def __init__(self):
        self.animal_channel = grpc.insecure_channel(
            ANIMAL_SERVICE_ADDRESS
        )

        self.animal_client = (
            animais_pb2_grpc.AnimalServiceStub(self.animal_channel)
        )

    def CreateAdoption(self, request, context):
        animal_id = request.animal_id.strip()
        adopter_name = request.adopter_name.strip()
        adopter_email = request.adopter_email.strip().lower()

        if not animal_id or not adopter_name or not adopter_email:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Animal, nome e e-mail são obrigatórios.",
            )

        if "@" not in adopter_email or "." not in adopter_email.split("@")[-1]:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "O e-mail informado é inválido.",
            )

        try:
            response = self.animal_client.GetAnimal(
                animais_pb2.GetAnimalRequest(
                    id=animal_id
                ),
                timeout=5,
            )

        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    "Animal não encontrado.",
                )

            if exc.code() == grpc.StatusCode.UNAVAILABLE:
                context.abort(
                    grpc.StatusCode.UNAVAILABLE,
                    "Microsserviço de Animais indisponível.",
                )

            context.abort(
                grpc.StatusCode.INTERNAL,
                "Falha ao consultar o animal.",
            )

        if not response.animal.available:
            context.abort(
                grpc.StatusCode.FAILED_PRECONDITION,
                "Este animal não está disponível para adoção.",
            )

        with SessionLocal() as db:
            adoption = Adoption(
                animal_id=animal_id,
                adopter_name=adopter_name,
                adopter_email=adopter_email,
                status="pendente",
            )

            db.add(adoption)
            db.commit()
            db.refresh(adoption)

            return adocao_pb2.AdoptionResponse(
                adoption=to_proto(adoption)
            )

    def GetAdoption(self, request, context):
        with SessionLocal() as db:
            adoption = db.get(Adoption, request.id)

            if adoption is None:
                context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    "Solicitação de adoção não encontrada.",
                )

            return adocao_pb2.AdoptionResponse(
                adoption=to_proto(adoption)
            )

    def ListAdoptions(self, request, context):
        with SessionLocal() as db:
            query = select(Adoption).order_by(
                Adoption.created_at.desc()
            )

            if request.status_filter:
                if request.status_filter not in VALID_STATUSES:
                    context.abort(
                        grpc.StatusCode.INVALID_ARGUMENT,
                        "Filtro de status inválido.",
                    )

                query = query.where(
                    Adoption.status == request.status_filter
                )

            adoptions = db.scalars(query).all()

            return adocao_pb2.ListAdoptionsResponse(
                adoptions=[to_proto(a) for a in adoptions]
            )

    def UpdateAdoptionStatus(self, request, context):
        new_status = request.status.strip().lower()

        if new_status not in VALID_STATUSES:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Status deve ser pendente, aprovada ou rejeitada.",
            )

        with SessionLocal() as db:
            # Bloqueia a solicitação durante a atualização.
            adoption = db.scalar(
                select(Adoption)
                .where(Adoption.id == request.id)
                .with_for_update()
            )

            if adoption is None:
                context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    "Solicitação de adoção não encontrada.",
                )

            # Repetir a mesma atualização não causa efeitos adicionais.
            if adoption.status == new_status:
                return adocao_pb2.AdoptionResponse(
                    adoption=to_proto(adoption)
                )

            # Somente solicitações pendentes podem ser finalizadas.
            if adoption.status != "pendente":
                context.abort(
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "Uma adoção finalizada não pode mudar de status.",
                )

            if new_status == "pendente":
                context.abort(
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "A solicitação já está pendente.",
                )

            # Rejeitar não altera a disponibilidade do animal.
            if new_status == "rejeitada":
                adoption.status = "rejeitada"

                db.commit()
                db.refresh(adoption)

                return adocao_pb2.AdoptionResponse(
                    adoption=to_proto(adoption)
                )

            # Aprovação: solicita a reserva via gRPC.
            try:
                reservation = self.animal_client.ReserveAnimal(
                    animais_pb2.ReserveAnimalRequest(
                        animal_id=adoption.animal_id,
                        adoption_id=adoption.id,
                    ),
                    timeout=5,
                )

            except grpc.RpcError as exc:
                if exc.code() == grpc.StatusCode.NOT_FOUND:
                    context.abort(
                        grpc.StatusCode.NOT_FOUND,
                        "Animal não encontrado.",
                    )

                if exc.code() == grpc.StatusCode.FAILED_PRECONDITION:
                    context.abort(
                        grpc.StatusCode.FAILED_PRECONDITION,
                        "Este animal já está indisponível ou foi adotado.",
                    )

                if exc.code() == grpc.StatusCode.INVALID_ARGUMENT:
                    context.abort(
                        grpc.StatusCode.INVALID_ARGUMENT,
                        "Dados da reserva inválidos.",
                    )

                context.abort(
                    grpc.StatusCode.UNAVAILABLE,
                    "Não foi possível confirmar a reserva do animal.",
                )

            # Reserva realizada: grava a aprovação.
            try:
                adoption.status = "aprovada"
                db.commit()

            except Exception:
                db.rollback()

                # Tenta desfazer uma reserva recém-criada
                # caso a gravação da adoção falhe.
                if reservation.newly_reserved:
                    try:
                        self.animal_client.ReleaseAnimal(
                            animais_pb2.ReleaseAnimalRequest(
                                animal_id=adoption.animal_id,
                                adoption_id=adoption.id,
                            ),
                            timeout=5,
                        )

                    except grpc.RpcError:
                        # A reserva mantém o adoption_id para
                        # permitir reconciliação posterior.
                        pass

                context.abort(
                    grpc.StatusCode.INTERNAL,
                    "Falha ao salvar a aprovação da adoção.",
                )

            db.refresh(adoption)

            return adocao_pb2.AdoptionResponse(
                adoption=to_proto(adoption)
            )


def serve():
    Base.metadata.create_all(bind=engine)

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    adocao_pb2_grpc.add_AdocaoServiceServicer_to_server(
        AdocaoService(),
        server,
    )

    server.add_insecure_port("[::]:50052")
    server.start()

    print("Microsserviço de Adoções iniciado na porta 50052.")

    try:
        server.wait_for_termination()
    finally:
        server.stop(0)


if __name__ == "__main__":
    serve()
