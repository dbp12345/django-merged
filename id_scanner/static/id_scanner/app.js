const payloadElement = document.getElementById("group-payload");
const groupData = payloadElement ? JSON.parse(payloadElement.textContent) : [];

const groupSelect = document.getElementById("group-select");
const templateSelect = document.getElementById("template-select");
const groupSteps = document.getElementById("group-steps");
const statusText = document.getElementById("status-text");
const submitButton = document.getElementById("submit-button");
const scanForm = document.getElementById("scan-form");
const resultFields = document.getElementById("result-fields");
const artifactGrid = document.getElementById("artifact-grid");
const confidencePill = document.getElementById("confidence-pill");

function csrfToken() {
  const cookieValue = `; ${document.cookie}`;
  const bits = cookieValue.split("; csrftoken=");
  if (bits.length !== 2) {
    return "";
  }
  return bits.pop().split(";").shift();
}

function setStatus(message) {
  statusText.textContent = message;
}

function renderTemplateOptions(groupId) {
  templateSelect.innerHTML = '<option value="">Select a template</option>';
  templateSelect.disabled = !groupId;

  const group = groupData.find((item) => String(item.id) === String(groupId));
  groupSteps.innerHTML = "";

  if (!group) {
    const item = document.createElement("li");
    item.textContent = "Select a group to view its enabled actions.";
    groupSteps.appendChild(item);
    return;
  }

  group.templates.forEach((template) => {
    const option = document.createElement("option");
    option.value = template.id;
    option.textContent = `${template.name} (${template.document_type})`;
    templateSelect.appendChild(option);
  });

  group.steps.forEach((step) => {
    const item = document.createElement("li");
    item.textContent = step;
    groupSteps.appendChild(item);
  });
}

function renderResultFields(fields) {
  resultFields.innerHTML = "";
  const keys = Object.keys(fields || {});
  if (!keys.length) {
    resultFields.innerHTML = '<p class="empty-state">No extracted fields returned.</p>';
    return;
  }

  keys.forEach((key) => {
    const field = fields[key];
    const article = document.createElement("article");
    article.className = "result-card";
    const heading = document.createElement("strong");
    heading.textContent = field.label || key;
    const valueLine = document.createElement("p");
    valueLine.textContent = field.value || "<empty>";
    const statusLine = document.createElement("p");
    const errorSuffix = field.errors && field.errors.length ? `: ${field.errors.join(" ")}` : "";
    statusLine.textContent = `${field.valid ? "Valid" : "Needs review"}${errorSuffix}`;
    article.appendChild(heading);
    article.appendChild(valueLine);
    article.appendChild(statusLine);
    resultFields.appendChild(article);
  });
}

function renderArtifacts(artifacts) {
  artifactGrid.innerHTML = "";
  const items = [
    { label: "Source", url: artifacts.source },
    { label: "Warped", url: artifacts.warped },
    { label: "Processed", url: artifacts.processed },
  ].filter((item) => item.url);

  if (!items.length) {
    artifactGrid.innerHTML = '<p class="empty-state">No artifact previews are available for this scan.</p>';
    return;
  }

  items.forEach((item) => {
    const article = document.createElement("article");
    article.className = "artifact-card";
    article.innerHTML = `
      <strong>${item.label}</strong>
      <img src="${item.url}" alt="${item.label} image">
    `;
    artifactGrid.appendChild(article);
  });
}

groupSelect.addEventListener("change", (event) => {
  renderTemplateOptions(event.target.value);
});

scanForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(scanForm);
  submitButton.disabled = true;
  setStatus("Scanning...");
  confidencePill.textContent = "Working";

  try {
    const response = await fetch("/id-scan/scan/", {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken() },
      body: formData,
      credentials: "same-origin",
    });

    const payload = await response.json();
    if (!response.ok || !payload.success) {
      throw new Error(payload.error || "Scan failed.");
    }

    confidencePill.textContent = `${payload.confidence_score.toFixed(2)}% confidence`;
    renderResultFields(payload.fields);
    renderArtifacts(payload.artifacts);
    setStatus(`Scan complete. Record #${payload.record_id}`);
  } catch (error) {
    confidencePill.textContent = "Error";
    renderResultFields({});
    renderArtifacts({});
    setStatus(error.message || "Scan failed.");
  } finally {
    submitButton.disabled = false;
  }
});

renderTemplateOptions("");
