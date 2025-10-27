importScripts('trackers.js');

let blockedCount = 0;
let whitelist = [];
let blacklist = [];

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ whitelist: [], blacklist: [], blockedCount: 0 });
});

function isTracker(url) {
  return trackerDomains.some(domain => url.includes(domain));
}

chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    const url = details.url;
    const domain = new URL(url).hostname;

    if (whitelist.includes(domain)) return; // don’t block

    if (isTracker(url) || blacklist.includes(domain)) {
      blockedCount++;
      chrome.action.setBadgeText({ text: blockedCount.toString() });
      chrome.action.setBadgeBackgroundColor({ color: "#d9534f" });

      chrome.storage.local.set({ blockedCount });
      return { cancel: true }; // block request
    }
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);

// Update whitelist/blacklist dynamically
chrome.storage.onChanged.addListener((changes) => {
  if (changes.whitelist) whitelist = changes.whitelist.newValue || [];
  if (changes.blacklist) blacklist = changes.blacklist.newValue || [];
});
