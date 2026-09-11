const fileInput = document.querySelector("#file-input");
const uploadArea = document.querySelector("#upload-area");

function addFiles(files) {
  for (const file of files) {
    if (!file.type.startsWith("image/")) continue;
    const item = document.createElement("p");
    item.textContent = `${file.name} selected`;
    document.querySelector("#label-items").append(item);
  }
  document.querySelector("#verify-button").disabled =
    document.querySelector("#label-items").children.length === 0;
}

fileInput.addEventListener("change", (event) => addFiles(event.target.files));
uploadArea.addEventListener("dragover", (event) => event.preventDefault());
uploadArea.addEventListener("drop", (event) => {
  event.preventDefault();
  addFiles(event.dataTransfer.files);
});
