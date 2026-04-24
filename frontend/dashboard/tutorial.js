(() => {
  const statusEl = document.getElementById('tutorialStatus');
  const fillBtn = document.getElementById('tutorialFillDhan');
  const activateBtn = document.getElementById('tutorialActivateDhan');
  const refreshBtn = document.getElementById('tutorialRefreshAll');

  const ids = {
    credsName: 'brokerCredentialsName',
    credsClient: 'brokerCredentialsClientId',
    credsKey: 'brokerCredentialsApiKey',
    credsAccess: 'brokerCredentialsAccessToken',
    setupName: 'brokerSetupName',
    setupLabel: 'brokerSetupAccountLabel',
    setupMode: 'brokerSetupExecutionMode',
    setupExchange: 'brokerSetupExchange',
    setupProduct: 'brokerSetupProductType',
    uiBroker: 'settingsWebhookBroker',
    webhookBroker: 'webhookBroker'
  };

  function el(id) { return document.getElementById(id); }
  function setStatus(msg) { if (statusEl) statusEl.textContent = msg; }
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  async function waitUntilEnabled(button, timeout = 10000) {
    const start = Date.now();
    while (button && button.disabled) {
      if (Date.now() - start > timeout) throw new Error('Timed out waiting for action to finish.');
      await sleep(150);
    }
  }

  async function clickAndWait(buttonId, timeout) {
    const button = el(buttonId);
    if (!button) throw new Error(`Missing button: ${buttonId}`);
    button.click();
    await waitUntilEnabled(button, timeout);
  }

  function applyDefaults() {
    el(ids.credsName).value = 'dhan';
    el(ids.setupName).value = 'dhan';
    el(ids.setupLabel).value = 'Dhan Live Account';
    el(ids.setupMode).value = 'live';
    el(ids.setupExchange).value = 'NSE';
    el(ids.setupProduct).value = 'cnc';
    el(ids.uiBroker).value = 'dhan';
    el(ids.webhookBroker).value = 'dhan';
  }

  async function verifyBroker() {
    const base = (el('apiBaseUrl')?.value || '').trim().replace(/\/$/, '');
    const res = await fetch(`${base}/brokers`);
    if (!res.ok) throw new Error(`Broker list failed: ${res.status}`);
    const data = await res.json();
    const brokers = Array.isArray(data.brokers) ? data.brokers : [];
    return brokers.includes('dhan');
  }

  if (fillBtn) {
    fillBtn.addEventListener('click', () => {
      applyDefaults();
      setStatus('Dhan defaults applied. Paste your values in Broker Credentials, then click Save & Activate Dhan.');
    });
  }

  if (activateBtn) {
    activateBtn.addEventListener('click', async () => {
      try {
        applyDefaults();
        setStatus('Saving credentials...');
        await clickAndWait('saveBrokerCredentials', 12000);
        setStatus('Saving broker setup...');
        await clickAndWait('saveBrokerSetup', 12000);
        setStatus('Refreshing broker list...');
        await clickAndWait('refreshBrokers', 10000);
        const ok = await verifyBroker();
        setStatus(ok ? 'Dhan is active. Use broker name dhan across the dashboard.' : 'Saved, but dhan is not yet visible in Brokers. Recheck the values and retry.');
      } catch (error) {
        setStatus(`Activation failed: ${error.message || error}`);
      }
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      try {
        setStatus('Refreshing health, brokers, orders, audit, summary, and charts...');
        await clickAndWait('refreshHealth', 8000);
        await clickAndWait('refreshBrokers', 8000);
        await clickAndWait('refreshOrders', 8000);
        await clickAndWait('refreshAudit', 8000);
        await clickAndWait('refreshSummary', 8000);
        await clickAndWait('refreshCharts', 8000);
        setStatus('Refresh complete.');
      } catch (error) {
        setStatus(`Refresh failed: ${error.message || error}`);
      }
    });
  }
})();
