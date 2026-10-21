
from contextlib import asynccontextmanager
from pathlib import Path

import logging
import grpc
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from gateway.auth import (
    authenticate_user,
    create_access_token,
    require_auth,
)
from gateway.schemas import (
    AdoptionCreate,
    AdoptionStatusUpdate,
    AnimalCreate,
    AnimalUpdate,
    LoginRequest,
)
from proto import animais_pb2, animais_pb2_grpc
from proto import adocao_pb2, adocao_pb2_grpc


load_dotenv()

logger = logging.getLogger("uvicorn.error")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

animal_channel = grpc.insecure_channel("localhost:50051")
adoption_channel = grpc.insecure_channel("localhost:50052")

animal_client = animais_pb2_grpc.AnimalServiceStub(animal_channel)
adoption_client = adocao_pb2_grpc.AdocaoServiceStub(adoption_channel)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    animal_channel.close()
    adoption_channel.close()


app = FastAPI(
    title="Sistema de Adoção de Animais",
    version="1.0.0",
    lifespan=lifespan,
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning(
        "HTTP 400 - Requisição inválida: %s %s | Erros: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )

    return JSONResponse(
        status_code=400,
        content={
            "detail": "Dados inválidos ou campos obrigatórios ausentes."
        },
    )

def call_grpc(operation):
    try:
        return operation()
    except grpc.RpcError as exc:
        code = exc.code()

        status_map = {
            grpc.StatusCode.INVALID_ARGUMENT: 400,
            grpc.StatusCode.NOT_FOUND: 404,
            grpc.StatusCode.FAILED_PRECONDITION: 409,
            grpc.StatusCode.ALREADY_EXISTS: 409,
            grpc.StatusCode.UNAVAILABLE: 503,
        }

        status = status_map.get(code, 502)
        detail = exc.details() or "Erro na comunicação gRPC."

        raise HTTPException(status_code=status, detail=detail) from exc


def animal_to_dict(animal):
    return {
        "id": animal.id,
        "name": animal.name,
        "species": animal.species,
        "breed": animal.breed,
        "age_years": animal.age_years,
        "description": animal.description,
        "available": animal.available,
    }


def adoption_to_dict(adoption):
    return {
        "id": adoption.id,
        "animal_id": adoption.animal_id,
        "adopter_name": adoption.adopter_name,
        "adopter_email": adoption.adopter_email,
        "status": adoption.status,
        "created_at": adoption.created_at,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/token")
def login(data: LoginRequest):
    if not authenticate_user(data.username, data.password):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data.username)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600,
    }


# ---------------- ANIMAIS ----------------

@app.post("/animais", status_code=201)
def create_animal(
    data: AnimalCreate,
    user: dict = Depends(require_auth),
):
    request = animais_pb2.CreateAnimalRequest(
        name=data.name,
        species=data.species,
        breed=data.breed,
        age_years=data.age_years,
        description=data.description,
    )

    response = call_grpc(
        lambda: animal_client.CreateAnimal(request, timeout=10)
    )

    return animal_to_dict(response.animal)


@app.get("/animais")
def list_animals(
    available_only: bool = False,
    user: dict = Depends(require_auth),
):
    request = animais_pb2.ListAnimalsRequest(
        available_only=available_only
    )

    response = call_grpc(
        lambda: animal_client.ListAnimals(request, timeout=10)
    )

    return [animal_to_dict(a) for a in response.animals]


@app.get("/animais/{animal_id}")
def get_animal(
    animal_id: str,
    user: dict = Depends(require_auth),
):
    request = animais_pb2.GetAnimalRequest(id=animal_id)

    response = call_grpc(
        lambda: animal_client.GetAnimal(request, timeout=10)
    )

    return animal_to_dict(response.animal)


@app.put("/animais/{animal_id}")
def update_animal(
    animal_id: str,
    data: AnimalUpdate,
    user: dict = Depends(require_auth),
):
    request = animais_pb2.UpdateAnimalRequest(
        id=animal_id,
        name=data.name,
        species=data.species,
        breed=data.breed,
        age_years=data.age_years,
        description=data.description,
        available=data.available,
    )

    response = call_grpc(
        lambda: animal_client.UpdateAnimal(request, timeout=10)
    )

    return animal_to_dict(response.animal)


# ---------------- ADOÇÕES ----------------

@app.post("/adocoes", status_code=201)
def create_adoption(
    data: AdoptionCreate,
    user: dict = Depends(require_auth),
):
    request = adocao_pb2.CreateAdoptionRequest(
        animal_id=data.animal_id,
        adopter_name=data.adopter_name,
        adopter_email=str(data.adopter_email),
    )

    response = call_grpc(
        lambda: adoption_client.CreateAdoption(request, timeout=10)
    )

    return adoption_to_dict(response.adoption)


@app.get("/adocoes")
def list_adoptions(
    status: str | None = Query(default=None),
    user: dict = Depends(require_auth),
):
    valid_statuses = {"pendente", "aprovada", "rejeitada"}

    if status is not None and status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="Status deve ser pendente, aprovada ou rejeitada.",
        )

    request = adocao_pb2.ListAdoptionsRequest(
        status_filter=status or ""
    )

    response = call_grpc(
        lambda: adoption_client.ListAdoptions(request, timeout=10)
    )

    return [adoption_to_dict(a) for a in response.adoptions]


@app.get("/adocoes/{adoption_id}")
def get_adoption(
    adoption_id: str,
    user: dict = Depends(require_auth),
):
    request = adocao_pb2.GetAdoptionRequest(id=adoption_id)

    response = call_grpc(
        lambda: adoption_client.GetAdoption(request, timeout=10)
    )

    return adoption_to_dict(response.adoption)


@app.patch("/adocoes/{adoption_id}/status")
def update_adoption_status(
    adoption_id: str,
    data: AdoptionStatusUpdate,
    user: dict = Depends(require_auth),
):
    request = adocao_pb2.UpdateAdoptionStatusRequest(
        id=adoption_id,
        status=data.status,
    )

    response = call_grpc(
        lambda: adoption_client.UpdateAdoptionStatus(
            request, timeout=10
        )
    )

    return adoption_to_dict(response.adoption)


if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
