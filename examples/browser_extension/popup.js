const note = document.querySelector("#note");
const status = document.querySelector("#status");

async function currentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function load() {
  const tab = await currentTab();
  const key = `note:${tab.url}`;
  document.querySelector("#page-title").textContent = tab.title || tab.url;
  const saved = await chrome.storage.local.get(key);
  note.value = saved[key] || "";
}

document.querySelector("#save").addEventListener("click", async () => {
  const tab = await currentTab();
  const key = `note:${tab.url}`;
  await chrome.storage.local.set({ [key]: note.value });
  status.textContent = "Saved on this device.";
});

load().catch((error) => { status.textContent = `Could not load: ${error.message}`; });
