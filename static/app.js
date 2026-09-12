const fileInput = document.querySelector("#file-input");
const uploadArea = document.querySelector("#upload-area");
const labelItems = document.querySelector("#label-items");
const verifyButton = document.querySelector("#verify-button");
const clearButton = document.querySelector("#clear-button");
const overallStatus = document.querySelector("#overall-status");
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

const SAMPLE_SCENARIOS = [
  {
    filename: "1_clean_pass.jpg",
    data: {
      brand_name: "OLD TOM DISTILLERY",
      class_type: "Kentucky Straight Bourbon Whiskey",
      alcohol_content: "45% Alc./Vol. (90 Proof)",
      net_contents: "750 mL",
      bottler_name_address: "Bottled by Old Tom Distilling Co., Louisville, KY",
      country_of_origin: "",
      is_import: false,
    },
  },
  {
    filename: "2_brand_case_diff.jpg",
    data: {
      brand_name: "Stone's Throw",
      class_type: "American Dry Gin",
      alcohol_content: "47% Alc./Vol.",
      net_contents: "750 mL",
      bottler_name_address: "Distilled by Stone's Throw Spirits, Portland, OR",
      country_of_origin: "",
      is_import: false,
    },
  },
  {
    filename: "3_warning_format_violation.jpg",
    data: {
      brand_name: "BLUE RIDGE RYE",
      class_type: "Straight Rye Whiskey",
      alcohol_content: "46% Alc./Vol.",
      net_contents: "750 mL",
      bottler_name_address: "Blue Ridge Distilling Co., Asheville, NC",
      country_of_origin: "",
      is_import: false,
    },
  },
  {
    filename: "4_abv_format_diff.jpg",
    data: {
      brand_name: "PRAIRIE HARVEST",
      class_type: "Vodka",
      alcohol_content: "80 Proof",
      net_contents: "750 mL",
      bottler_name_address: "Prairie Harvest Distilling, Omaha, NE",
      country_of_origin: "",
      is_import: false,
    },
  },
  {
    filename: "5_missing_country_of_origin.jpg",
    data: {
      brand_name: "HIGHLAND RESERVE",
      class_type: "Single Malt Scotch Whisky",
      alcohol_content: "43% Alc./Vol.",
      net_contents: "700 mL",
      bottler_name_address: "Highland Distillers Ltd., Edinburgh, Scotland",
      country_of_origin: "",
      is_import: true,
    },
  },
  {
    filename: "6_genuine_mismatch.jpg",
    data: {
      brand_name: "SILVER SHORES TEQUILA",
      class_type: "Dark Rum",
      alcohol_content: "40% Alc./Vol.",
      net_contents: "750 mL",
      bottler_name_address: "Oak & Iron Distilling Co., Tampa, FL",
      country_of_origin: "",
      is_import: false,
    },
  },
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
  input.value = item.data[key] || "";
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

  const contentColumn = document.createElement("div");
  contentColumn.className = "card-content";
  contentColumn.append(form);

  const cardResults = document.createElement("div");
  cardResults.className = "card-results";
  cardResults.style.display = "none";
  contentColumn.append(cardResults);

  article.append(previewColumn, contentColumn);
  labelItems.append(article);
}

function updateVerifyButton() {
  verifyButton.disabled = items.length === 0;
}

function addFiles(files) {
  for (const file of files) {
    if (!file.type.startsWith("image/")) {
      setMessage(`${file.name} was skipped because it doesn't appear to be an image.`);
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
  overallStatus.style.display = "none";
  overallStatus.className = "overall-indicator";
  overallStatus.textContent = "";

  const allCardResults = labelItems.querySelectorAll(".card-results");
  for (const cr of allCardResults) {
    cr.replaceChildren();
    cr.style.display = "none";
  }

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
  if (overallStatus) {
    overallStatus.className = `overall-indicator status-${body.status}`;
    overallStatus.textContent = `Overall: ${statusLabel(body.status)}`;
    overallStatus.style.display = "inline-flex";
  }

  const articles = labelItems.querySelectorAll(".label-item");

  for (const result of body.results || []) {
    const card = articles[result.item_index];
    if (!card) continue;

    const cardResults = card.querySelector(".card-results");
    if (!cardResults) continue;
    cardResults.replaceChildren();

    const resultBox = document.createElement("div");
    resultBox.className = `result-item status-${result.status}`;

    const title = document.createElement("h3");
    title.textContent = `Label ${result.item_index + 1}: ${statusLabel(result.status)}`;
    resultBox.append(title);

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
    resultBox.append(fieldList);
    cardResults.append(resultBox);
    cardResults.style.display = "block";
  }
}

function clearAll() {
  for (const item of items) {
    if (item.previewUrl && item.previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(item.previewUrl);
    }
  }
  items.length = 0;
  labelItems.replaceChildren();
  if (overallStatus) {
    overallStatus.style.display = "none";
    overallStatus.className = "overall-indicator";
    overallStatus.textContent = "";
  }
  setMessage("");
  updateVerifyButton();
}

if (clearButton) {
  clearButton.addEventListener("click", clearAll);
}

async function loadSampleScenarios() {
  for (const scenario of SAMPLE_SCENARIOS) {
    try {
      const sampleUrl = `/samples/${scenario.filename}`;
      const response = await fetch(sampleUrl);
      if (!response.ok) continue;
      const blob = await response.blob();
      const file = new File([blob], scenario.filename, { type: blob.type || "image/jpeg" });
      const item = {
        id: crypto.randomUUID(),
        file,
        previewUrl: sampleUrl,
        data: { ...scenario.data },
      };
      items.push(item);
      renderItem(item);
    } catch (err) {
      console.warn("Could not load sample:", scenario.filename, err);
    }
  }
  updateVerifyButton();
}

loadSampleScenarios();
