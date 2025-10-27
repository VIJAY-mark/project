document.addEventListener('DOMContentLoaded', async () => {
  const countEl = document.getElementById('count');
  const domainInput = document.getElementById('domain');
  const addWhitelist = document.getElementById('addWhitelist');
  const addBlacklist = document.getElementById('addBlacklist');
  const whitelistEl = document.getElementById('whitelist');
  const blacklistEl = document.getElementById('blacklist');

  let { blockedCount = 0, whitelist = [], blacklist = [] } = await chrome.storage.local.get();

  countEl.textContent = blockedCount;
  updateLists();

  addWhitelist.addEventListener('click', () => addDomain('whitelist'));
  addBlacklist.addEventListener('click', () => addDomain('blacklist'));

  async function addDomain(type) {
    const domain = domainInput.value.trim();
    if (!domain) return;

    const list = type === 'whitelist' ? whitelist : blacklist;
    if (!list.includes(domain)) {
      list.push(domain);
      await chrome.storage.local.set({ [type]: list });
      updateLists();
    }
    domainInput.value = '';
  }

  function updateLists() {
    whitelistEl.innerHTML = whitelist.map(d => `<li>${d}</li>`).join('');
    blacklistEl.innerHTML = blacklist.map(d => `<li>${d}</li>`).join('');
  }
});
