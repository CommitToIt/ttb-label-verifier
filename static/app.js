const fileInput = document.querySelector("#file-input");
const uploadArea = document.querySelector("#upload-area");
const labelItems = document.querySelector("#label-items");
const verifyButton = document.querySelector("#verify-button");
const results = document.querySelector("#results");
const requestMessage = document.querySelector("#request-message");
const MAX_FILE_SIZE = 10 * 1024 * 1024;
const items = [];

const fields = [
  ["brand_name", "Brand name"],
  ["class_type", "Class/type"],
  ["alcohol_content", "Alcohol content"],
  ["net_contents", "Net contents"],
  ["bottler_name_address", "Bottler name/address"],
  ["country_of_origin", "Country of origin"],
];

function setMessage(message = "") {
  requestMessage.textContent = message;
}

function makeInput(item, key, labelText) {
  const label = document.createElement("label");
  label.textContent = labelText;
  const input = document.createElement("input");
  input.type = "text";
  input.name = key;
  input.autocomplete = "off";
  input.addEventListener("input", () => { item.data[key] = input.value; });
  label.append(input);
  return label;
}

function renderItem(item) {
  const article = document.createElement("article");
  article.className = "label-item";
  article.dataset.itemId = item.id;

  const previewColumn = document.createElement("div");
  const preview = document.createElement("img");
  preview.className = "preview";
  preview.src = item.previewUrl;
  preview.alt = `Preview of ${item.file.name}`;
  const fileName = document.createElement("p");
  fileName.className = "file-name";
  fileName.textContent = item.file.name;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "remove-button";
  remove.textContent = "Remove image";
  remove.addEventListener("click", () => {
    URL.revokeObjectURL(item.previewUrl);
    items.splice(items.indexOf(item), 1);
    article.remove();
    updateVerifyButton();
  });
  previewColumn.append(preview, fileName, remove);

  const form = document.createElement("div");
  form.className = "form-grid";
  for (const [key, labelText] of fields) form.append(makeInput(item, key, labelText));

  const importWrapper = document.createElement("div");
  importWrapper.className = "import-control";
  const importLabel = document.createElement("label");
  const importInput = document.createElement("input");
  importInput.type = "checkbox";
  importInput.checked = item.data.is_import;
  importInput.addEventListener("change", () => {
    item.data.is_import = importInput.checked;
    countryInput.disabled = !importInput.checked;
    if (!importInput.checked) {
      countryInput.value = "";
      item.data.country_of_origin = "";
    }
  });
  importLabel.append(importInput, document.createTextNode("This is an import"));
  importWrapper.append(importLabel);
  form.append(importWrapper);

  const countryInput = form.querySelector('input[name="country_of_origin"]');
  countryInput.disabled = !item.data.is_import;
  article.append(previewColumn, form);
  labelItems.append(article);
}

function updateVerifyButton() {
  verifyButton.disabled = items.length === 0;
}

function addFiles(files) {
  for (const file of files) {
    if (!file.type.startsWith("image/")) {
      setMessage(`${file.name} was skipped because it is not an image.`);
      continue;
    }
    if (file.size > MAX_FILE_SIZE) {
      setMessage(`${file.name} was skipped because it exceeds the 10 MB limit.`);
      continue;
    }
    const item = {
      id: crypto.randomUUID(),
      file,
      previewUrl: URL.createObjectURL(file),
      data: {
        brand_name: "",
        class_type: "",
        alcohol_content: "",
        net_contents: "",
        bottler_name_address: "",
        country_of_origin: "",
        is_import: false,
      },
    };
    items.push(item);
    renderItem(item);
  }
  updateVerifyButton();
}

fileInput.addEventListener("change", (event) => addFiles(event.target.files));
uploadArea.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadArea.classList.add("is-dragging");
});
uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("is-dragging"));
uploadArea.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadArea.classList.remove("is-dragging");
  addFiles(event.dataTransfer.files);
});

verifyButton.addEventListener("click", async () => {
  verifyButton.disabled = true;
  setMessage("Verifying labels...");
  results.replaceChildren();
  const formData = new FormData();
  for (const item of items) formData.append("images", item.file, item.file.name);
  formData.append("applications", JSON.stringify(items.map((item) => item.data)));

  try {
    const response = await fetch("/api/verify", { method: "POST", body: formData });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Verification request failed.");
    renderResults(body);
    setMessage("Verification complete.");
  } catch (error) {
    setMessage(error.message || "Verification request failed.");
  } finally {
    updateVerifyButton();
  }
});

function statusLabel(status) {
  return status === "needs-review" ? "Needs review" : status.charAt(0).toUpperCase() + status.slice(1);
}

function renderResults(body) {
  const heading = document.createElement("h2");
  heading.textContent = "Verification results";
  const overall = document.createElement("div");
  overall.className = `overall status-${body.status}`;
  overall.textContent = `Overall: ${statusLabel(body.status)}`;
  const list = document.createElement("div");
  list.className = "result-list";

  for (const result of body.results || []) {
    const item = document.createElement("article");
    item.className = `result-item status-${result.status}`;
    const title = document.createElement("h3");
    title.textContent = `Label ${result.item_index + 1}: ${statusLabel(result.status)}`;
    item.append(title);
    const fieldList = document.createElement("div");
    fieldList.className = "field-results";
    for (const [name, field] of Object.entries(result.fields || {})) {
      const fieldElement = document.createElement("div");
      fieldElement.className = `field-result status-${field.status}`;
      const fieldName = document.createElement("span");
      fieldName.className = "field-name";
      fieldName.textContent = name.replaceAll("_", " ");
      const fieldStatus = document.createElement("strong");
      fieldStatus.textContent = statusLabel(field.status);
      fieldElement.append(fieldName, fieldStatus);
      if (field.reason) {
        const reason = document.createElement("span");
        reason.className = "field-reason";
        reason.textContent = field.reason;
        fieldElement.append(reason);
      }
      fieldList.append(fieldElement);
    }
    item.append(fieldList);
    list.append(item);
  }
  results.append(heading, overall, list);
}
