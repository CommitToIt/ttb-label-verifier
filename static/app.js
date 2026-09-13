const fileInput = document.querySelector("#file-input");
const uploadArea = document.querySelector("#upload-area");
const labelItems = document.querySelector("#label-items");
const verifyButton = document.querySelector("#verify-button");
const clearButton = document.querySelector("#clear-button");
const overallStatus = document.querySelector("#overall-status");
const requestMessage = document.querySelector("#request-message");
const lightbox = document.querySelector("#lightbox");
const lightboxImg = document.querySelector("#lightbox-img");
const uploadDisclaimer = document.querySelector("#upload-disclaimer");
let MAX_FILE_SIZE = 10 * 1024 * 1024;
let MAX_BATCH_SIZE = 20;
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
    filename: "1_all_fields_match_pass.jpg",
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
    filename: "2_brand_name_case_difference_pass.jpg",
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
    filename: "3_warning_not_bold_caps_fail.jpg",
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
    filename: "4_alcohol_proof_format_pass.jpg",
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
    filename: "5_import_missing_country_fail.jpg",
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
    filename: "6_brand_name_mismatch_fail.jpg",
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
  {
    filename: "7_real_photo_bourbon_pass.jpg",
    data: {
      brand_name: "Buffalo Trace",
      class_type: "Kentucky Straight Bourbon Whiskey",
      alcohol_content: "45",
      net_contents: "750",
      bottler_name_address: "Buffalo Trace Distillery, Frankfort, KY",
      country_of_origin: "",
      is_import: false,
    },
  },
  {
    filename: "8_real_photo_beer_pass.jpg",
    data: {
      brand_name: "Devils Backbone",
      class_type: "India Pale Ale",
      alcohol_content: "7",
      net_contents: "12 fl oz",
      bottler_name_address: "Devils Backbone Brewing Company, Lexington, VA",
      country_of_origin: "",
      is_import: false,
    },
  },
];

function setMessage(message = "") {
  requestMessage.textContent = message;
}

function makeFieldGroup(item, key, labelText) {
  const group = document.createElement("div");
  group.className = "field-group";
  group.dataset.fieldKey = key;

  const header = document.createElement("div");
  header.className = "field-header";

  const label = document.createElement("label");
  label.className = "field-label";
  label.textContent = labelText;
  label.htmlFor = `input-${item.id}-${key}`;

  header.append(label);

  const reason = document.createElement("div");
  reason.className = "field-reason";
  reason.style.display = "none";

  const input = document.createElement("input");
  input.type = "text";
  input.id = `input-${item.id}-${key}`;
  input.name = key;
  input.value = item.data[key] || "";
  input.autocomplete = "off";
  if (key === "net_contents") {
    input.placeholder = "e.g., 750 mL or 12 FL OZ";
  } else if (key === "alcohol_content") {
    input.placeholder = "e.g., 45% or 90 Proof";
  }
  input.addEventListener("input", () => { item.data[key] = input.value; });

  group.append(header, reason, input);
  return group;
}

function openLightbox(url, altText) {
  if (!lightbox || !lightboxImg) return;
  lightboxImg.src = url;
  lightboxImg.alt = altText || "Enlarged label view";
  lightbox.classList.add("is-open");
  lightbox.setAttribute("aria-hidden", "false");
}

function closeLightbox() {
  if (!lightbox) return;
  lightbox.classList.remove("is-open");
  lightbox.setAttribute("aria-hidden", "true");
  if (lightboxImg) lightboxImg.src = "";
}

if (lightbox) {
  lightbox.addEventListener("click", closeLightbox);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && lightbox.classList.contains("is-open")) {
      closeLightbox();
    }
  });
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
  preview.title = "Click to enlarge";
  preview.addEventListener("click", () => openLightbox(item.previewUrl, `Enlarged view of ${item.file.name}`));
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

  const contentColumn = document.createElement("div");
  contentColumn.className = "card-content";

  const cardHeader = document.createElement("div");
  cardHeader.className = "card-header";
  const cardTitle = document.createElement("h3");
  cardTitle.className = "card-title";
  cardTitle.textContent = `Label ${items.indexOf(item) + 1}`;
  const cardBadge = document.createElement("span");
  cardBadge.className = "card-badge";
  cardHeader.append(cardTitle, cardBadge);
  contentColumn.append(cardHeader);

  const form = document.createElement("div");
  form.className = "form-grid";
  for (const [key, labelText] of fields) form.append(makeFieldGroup(item, key, labelText));

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

  contentColumn.append(form);

  const warningSection = document.createElement("div");
  warningSection.className = "warning-section";
  const warnHeading = document.createElement("h4");
  warnHeading.className = "warning-heading";
  warnHeading.textContent = "Government warning";
  const warnGrid = document.createElement("div");
  warnGrid.className = "warning-grid";
  warningSection.append(warnHeading, warnGrid);
  contentColumn.append(warningSection);

  article.append(previewColumn, contentColumn);
  labelItems.append(article);
}

function updateVerifyButton() {
  verifyButton.disabled = items.length === 0;
}

function addFiles(files) {
  for (const file of files) {
    if (items.length >= MAX_BATCH_SIZE) {
      setMessage(`Batch limit reached. Maximum ${MAX_BATCH_SIZE} images per batch.`);
      break;
    }
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

function resetCardResults() {
  const articles = labelItems.querySelectorAll(".label-item");
  for (const card of articles) {
    const cardBadge = card.querySelector(".card-badge");
    if (cardBadge) {
      cardBadge.style.display = "none";
      cardBadge.className = "card-badge";
      cardBadge.textContent = "";
    }

    const fieldGroups = card.querySelectorAll(".field-group");
    for (const fg of fieldGroups) {
      const header = fg.querySelector(".field-header");
      if (header) {
        header.className = "field-header";
      }
      const reason = fg.querySelector(".field-reason");
      if (reason) {
        reason.style.display = "none";
        reason.textContent = "";
      }
    }

    const warnSection = card.querySelector(".warning-section");
    if (warnSection) {
      warnSection.style.display = "none";
      const warnGrid = warnSection.querySelector(".warning-grid");
      if (warnGrid) warnGrid.replaceChildren();
    }
  }
}

verifyButton.addEventListener("click", async () => {
  verifyButton.disabled = true;
  setMessage("Verifying labels...");
  if (overallStatus) {
    overallStatus.style.display = "none";
    overallStatus.className = "overall-indicator";
    overallStatus.textContent = "";
  }
  resetCardResults();

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

    // 1. Card overall status badge at top
    const cardBadge = card.querySelector(".card-badge");
    if (cardBadge) {
      cardBadge.className = `card-badge badge-${result.status}`;
      cardBadge.textContent = statusLabel(result.status);
      cardBadge.style.display = "inline-block";
    }

    const fieldResults = result.fields || {};

    // 2 & 3. Populate each form field's status background and reason directly above input
    const formFieldKeys = [
      "brand_name",
      "class_type",
      "alcohol_content",
      "net_contents",
      "bottler_name_address",
      "country_of_origin",
    ];

    for (const key of formFieldKeys) {
      const fieldGroup = card.querySelector(`.field-group[data-field-key="${key}"]`);
      if (!fieldGroup) continue;

      const fResult = fieldResults[key];
      const header = fieldGroup.querySelector(".field-header");
      const reasonEl = fieldGroup.querySelector(".field-reason");

      // country_of_origin only shows if it was evaluated (is_import was true)
      if (fResult && (key !== "country_of_origin" || result.submitted?.is_import)) {
        if (header) {
          header.className = `field-header header-${fResult.status}`;
        }
        if (reasonEl) {
          if (fResult.reason) {
            reasonEl.textContent = fResult.reason;
            reasonEl.style.display = "block";
          } else {
            reasonEl.style.display = "none";
            reasonEl.textContent = "";
          }
        }
      } else {
        if (header) {
          header.className = "field-header";
        }
        if (reasonEl) {
          reasonEl.style.display = "none";
          reasonEl.textContent = "";
        }
      }
    }

    // 4. Warning section for warning text & formatting results
    const warnSection = card.querySelector(".warning-section");
    const warnGrid = card.querySelector(".warning-grid");
    if (warnSection && warnGrid) {
      warnGrid.replaceChildren();
      const warnFields = [
        ["government_warning_text", "Statutory Warning Text"],
        ["government_warning_is_bold_and_caps", "Heading Format (Bold & Caps)"],
      ];

      let hasWarningResults = false;
      for (const [wKey, wLabel] of warnFields) {
        const wResult = fieldResults[wKey];
        if (!wResult) continue;
        hasWarningResults = true;

        const wItem = document.createElement("div");
        wItem.className = `warning-item status-${wResult.status}`;

        const wHeader = document.createElement("div");
        wHeader.className = "field-header";

        const wLabelEl = document.createElement("span");
        wLabelEl.className = "field-label";
        wLabelEl.textContent = wLabel;

        const wBadge = document.createElement("span");
        wBadge.className = `field-badge status-${wResult.status}`;
        wBadge.textContent = statusLabel(wResult.status);

        wHeader.append(wLabelEl, wBadge);
        wItem.append(wHeader);

        if (wResult.reason) {
          const wReason = document.createElement("div");
          wReason.className = "field-reason";
          wReason.textContent = wResult.reason;
          wItem.append(wReason);
        }

        warnGrid.append(wItem);
      }

      // Also display image_upload or processing_error if present
      for (const errKey of ["image_upload", "processing_error"]) {
        const errResult = fieldResults[errKey];
        if (!errResult) continue;
        hasWarningResults = true;

        const errItem = document.createElement("div");
        errItem.className = `warning-item status-${errResult.status}`;

        const errHeader = document.createElement("div");
        errHeader.className = "field-header";

        const errLabelEl = document.createElement("span");
        errLabelEl.className = "field-label";
        errLabelEl.textContent = errKey.replace("_", " ");

        const errBadge = document.createElement("span");
        errBadge.className = `field-badge status-${errResult.status}`;
        errBadge.textContent = statusLabel(errResult.status);

        errHeader.append(errLabelEl, errBadge);
        errItem.append(errHeader);

        if (errResult.reason) {
          const errReason = document.createElement("div");
          errReason.className = "field-reason";
          errReason.textContent = errResult.reason;
          errItem.append(errReason);
        }

        warnGrid.append(errItem);
      }

      warnSection.style.display = hasWarningResults ? "block" : "none";
    }
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

async function initConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) return;
    const cfg = await res.json();
    if (cfg.max_batch_size) MAX_BATCH_SIZE = cfg.max_batch_size;
    if (cfg.max_upload_size_bytes) MAX_FILE_SIZE = cfg.max_upload_size_bytes;
    if (uploadDisclaimer) {
      const mb = Math.round(MAX_FILE_SIZE / (1024 * 1024));
      uploadDisclaimer.textContent = `Accepts JPEG, PNG, GIF, WebP, BMP, or TIFF images, up to ${mb}MB (up to ${MAX_BATCH_SIZE} images per batch)`;
    }
  } catch (err) {
    console.warn("Could not load /api/config:", err);
  }
}

initConfig();
loadSampleScenarios();
