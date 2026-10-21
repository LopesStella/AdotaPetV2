
const $ = (selector) => document.querySelector(selector);

let token = sessionStorage.getItem("adotapet_token") || "";
let username = sessionStorage.getItem("adotapet_user") || "";
let animaisCache = [];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function nomeAnimal(animalId) {
  const animal = animaisCache.find(a => a.id === animalId);

  if (!animal) {
    return `Animal não encontrado (${animalId})`;
  }

  const especie =
    animal.species === "cachorro" ? "Cachorro" :
    animal.species === "gato" ? "Gato" :
    animal.species;

  return `${animal.name} — ${especie}`;
}

function message(selector, text, type = "") {
  const element = $(selector);
  element.textContent = text;
  element.className = `message ${type}`.trim();
}

async function api(path, method = "GET", body = null) {
  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (body !== null) {
    headers["Content-Type"] = "application/json";
  }

  let response;

  try {
    response = await fetch(path, {
      method,
      headers,
      body: body === null ? undefined : JSON.stringify(body)
    });
  } catch {
    throw new Error("Não foi possível conectar ao Gateway.");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/token") {
      logout();
      throw new Error("Sessão inválida ou expirada. Faça login novamente.");
    }

    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : `Erro HTTP ${response.status}. Verifique os dados enviados.`
    );
  }

  return data;
}

function showApp() {
  $("#login-section").classList.add("hidden");
  $("#app-section").classList.remove("hidden");
  $("#user-area").classList.remove("hidden");
  $("#user-name").textContent = username;
}

function logout() {
  token = "";
  username = "";
  animaisCache = [];

  sessionStorage.removeItem("adotapet_token");
  sessionStorage.removeItem("adotapet_user");

  $("#login-section").classList.remove("hidden");
  $("#app-section").classList.add("hidden");
  $("#user-area").classList.add("hidden");
  $("#password").value = "";
}

$("#logout-button").addEventListener("click", logout);

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const button = event.submitter;
  button.disabled = true;
  message("#login-message", "Validando acesso...");

  try {
    const enteredUsername = $("#username").value.trim();
    const enteredPassword = $("#password").value;

    const result = await api("/auth/token", "POST", {
      username: enteredUsername,
      password: enteredPassword
    });

    if (!result.access_token) {
      throw new Error("O Gateway não retornou um token.");
    }

    token = result.access_token;
    username = enteredUsername;

    sessionStorage.setItem("adotapet_token", token);
    sessionStorage.setItem("adotapet_user", username);

    message("#login-message", "");
    showApp();

    await loadAnimals();
    await loadAdoptions();
  } catch (error) {
    message("#login-message", error.message, "error");
    console.error("Erro no login:", error);
  } finally {
    button.disabled = false;
  }
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.classList.toggle("active", tab === button);
    });

    $("#animals-panel").classList.toggle(
      "hidden", button.dataset.tab !== "animals"
    );

    $("#adoptions-panel").classList.toggle(
      "hidden", button.dataset.tab !== "adoptions"
    );
  });
});

async function loadAnimals() {
  const container = $("#animals-list");
  container.textContent = "Carregando animais...";

  try {
    const animals = await api("/animais");

    animaisCache = animals;
    container.innerHTML = "";

    if (animals.length === 0) {
      container.textContent = "Nenhum animal cadastrado.";
    }

    const select = $("#adoption-animal");
    const previous = select.value;
    select.innerHTML = '<option value="">Selecione um animal</option>';

    animals.forEach((animal) => {
      if (animal.available) {
        const option = document.createElement("option");
        option.value = animal.id;
        option.textContent = `${animal.name} - ${animal.species}`;
        select.appendChild(option);
      }

      const card = document.createElement("article");
      card.className = "card";

      card.innerHTML = `
        <div class="card-icon">
          ${animal.species === "gato" ? "🐱" : "🐶"}
        </div>
        <h3>${escapeHtml(animal.name)}</h3>
        <p><strong>Espécie:</strong> ${escapeHtml(animal.species)}</p>
        <p><strong>Raça:</strong> ${escapeHtml(animal.breed)}</p>
        <p><strong>Idade:</strong> ${animal.age_years} ano(s)</p>
        <p class="description">${escapeHtml(animal.description)}</p>
        <span class="status ${animal.available ? "available" : "unavailable"}">
          ${animal.available ? "Disponível" : "Indisponível"}
        </span>
        <div class="card-actions">
          <button class="btn btn-light toggle-availability">
            ${animal.available ? "Marcar indisponível" : "Marcar disponível"}
          </button>
        </div>
      `;

      card.querySelector(".toggle-availability").addEventListener(
        "click", async (event) => {
          const button = event.currentTarget;
          button.disabled = true;

          try {
            await api(`/animais/${encodeURIComponent(animal.id)}`, "PUT", {
              name: animal.name,
              species: animal.species,
              breed: animal.breed,
              age_years: animal.age_years,
              description: animal.description,
              available: !animal.available
            });

            await loadAnimals();
            await loadAdoptions();
          } catch (error) {
            alert(error.message);
            button.disabled = false;
          }
        }
      );

      container.appendChild(card);
    });

    if ([...select.options].some((option) => option.value === previous)) {
      select.value = previous;
    }
  } catch (error) {
    container.textContent = error.message;
    throw error;
  }
}

$("#animal-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const button = event.submitter;
  button.disabled = true;
  message("#animal-message", "Cadastrando animal...");

  try {
    await api("/animais", "POST", {
      name: $("#animal-name").value.trim(),
      species: $("#animal-species").value,
      breed: $("#animal-breed").value.trim(),
      age_years: Number($("#animal-age").value),
      description: $("#animal-description").value.trim()
    });

    event.target.reset();
    message("#animal-message", "Animal cadastrado com sucesso!", "success");

    await loadAnimals();
    await loadAdoptions();
  } catch (error) {
    message("#animal-message", error.message, "error");
  } finally {
    button.disabled = false;
  }
});

async function loadAdoptions() {
  const container = $("#adoptions-list");
  container.textContent = "Carregando adoções...";

  try {
    // Carrega todos os animais, inclusive os indisponíveis,
    // para identificar corretamente as adoções antigas.
    const animals = await api("/animais");
    animaisCache = animals;

    const adoptions = await api("/adocoes");
    container.innerHTML = "";

    if (adoptions.length === 0) {
      container.textContent = "Nenhuma solicitação cadastrada.";
    }

    adoptions.forEach((adoption) => {
      const card = document.createElement("article");
      card.className = "card";

      card.innerHTML = `
        <h3>Solicitação de adoção</h3>
        <p><strong>Adotante:</strong> ${escapeHtml(adoption.adopter_name)}</p>
        <p><strong>E-mail:</strong> ${escapeHtml(adoption.adopter_email)}</p>
        <p><strong>Animal:</strong> ${escapeHtml(nomeAnimal(adoption.animal_id))}</p>
        <p>
          <span class="status ${escapeHtml(adoption.status)}">
            ${escapeHtml(adoption.status)}
          </span>
        </p>
        <label>Atualizar status</label>
        <div class="card-actions">
          <select class="status-select">
            <option value="pendente">Pendente</option>
            <option value="aprovada">Aprovada</option>
            <option value="rejeitada">Rejeitada</option>
          </select>
          <button class="btn btn-light save-status">Salvar</button>
        </div>
      `;

      const select = card.querySelector(".status-select");
      select.value = adoption.status;

      card.querySelector(".save-status").addEventListener(
        "click", async (event) => {
          const button = event.currentTarget;
          button.disabled = true;

          try {
            await api(
              `/adocoes/${encodeURIComponent(adoption.id)}/status`,
              "PATCH",
              { status: select.value }
            );

            await loadAnimals();
            await loadAdoptions();
          } catch (error) {
            alert(error.message);
            button.disabled = false;
          }
        }
      );

      container.appendChild(card);
    });
  } catch (error) {
    container.textContent = error.message;
  }
}

$("#adoption-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const button = event.submitter;
  button.disabled = true;
  message("#adoption-message", "Enviando solicitação...");

  try {
    await api("/adocoes", "POST", {
      animal_id: $("#adoption-animal").value,
      adopter_name: $("#adopter-name").value.trim(),
      adopter_email: $("#adopter-email").value.trim()
    });

    event.target.reset();
    message("#adoption-message", "Adoção solicitada com sucesso!", "success");

    await loadAnimals();
    await loadAdoptions();
  } catch (error) {
    message("#adoption-message", error.message, "error");
  } finally {
    button.disabled = false;
  }
});

$("#refresh-animals").addEventListener("click", async () => {
  try {
    await loadAnimals();
    await loadAdoptions();
  } catch (error) {
    console.error("Erro ao atualizar animais:", error);
  }
});

$("#refresh-adoptions").addEventListener("click", loadAdoptions);

if (token && username) {
  showApp();

  loadAnimals()
    .then(loadAdoptions)
    .catch((error) => {
      console.error("Erro ao carregar dados:", error);
    });
}
