/**
 * Miruboard Card for Home Assistant
 * Combines crypto, travel time, RSS, and calendar widgets in one card.
 *
 * Installation: Copy to /config/www/miruboard-card.js
 * Add to Lovelace resources: /local/miruboard-card.js (JavaScript Module)
 */

const LitElement = customElements.get("ha-panel-lovelace")
  ? Object.getPrototypeOf(customElements.get("ha-panel-lovelace"))
  : Object.getPrototypeOf(customElements.get("hc-lovelace"));

const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

// ============================================================
// MIRUBOARD CRYPTO CARD
// ============================================================
class MiruboardCryptoCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      _config: { type: Object },
    };
  }

  setConfig(config) {
    if (!config.entities || !config.entities.length) {
      throw new Error("Please define crypto entities");
    }
    this._config = {
      title: "Crypto",
      ...config,
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      ha-card {
        padding: 16px;
        background: var(--card-background-color);
      }
      .header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 500;
        color: var(--secondary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .header ha-icon {
        --mdc-icon-size: 18px;
      }
      .coins {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .coin {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 12px;
        border-radius: 12px;
        background: var(--primary-background-color);
        transition: background 0.2s;
      }
      .coin:hover {
        background: var(--secondary-background-color);
      }
      .coin-left {
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .coin-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--primary-color);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 12px;
      }
      .coin-name {
        font-weight: 600;
        font-size: 14px;
        color: var(--primary-text-color);
      }
      .coin-right {
        text-align: right;
      }
      .coin-price {
        font-weight: 700;
        font-size: 15px;
        color: var(--primary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .coin-change {
        font-size: 12px;
        font-weight: 500;
        margin-top: 2px;
      }
      .coin-change.positive {
        color: #22c55e;
      }
      .coin-change.negative {
        color: #ef4444;
      }
    `;
  }

  render() {
    if (!this.hass || !this._config) return html``;

    const entities = this._config.entities || [];

    return html`
      <ha-card>
        <div class="header">
          <ha-icon icon="mdi:chart-line"></ha-icon>
          ${this._config.title}
        </div>
        <div class="coins">
          ${entities.map((entityId) => {
            const state = this.hass.states[entityId];
            if (!state) return html``;

            const price = parseFloat(state.state) || 0;
            const change = state.attributes.change_24h || 0;
            const coinId = state.attributes.coin_id || "";
            const symbol = coinId.substring(0, 3).toUpperCase();
            const isPositive = change >= 0;

            // Format price
            const formattedPrice =
              price >= 1
                ? price.toLocaleString("nl-NL", {
                    style: "currency",
                    currency: "EUR",
                    minimumFractionDigits: 2,
                  })
                : `€${price.toFixed(4)}`;

            return html`
              <div class="coin">
                <div class="coin-left">
                  <div class="coin-icon">${symbol}</div>
                  <div class="coin-name">
                    ${state.attributes.friendly_name?.replace("Miruboard ", "") || coinId}
                  </div>
                </div>
                <div class="coin-right">
                  <div class="coin-price">${formattedPrice}</div>
                  <div
                    class="coin-change ${isPositive ? "positive" : "negative"}"
                  >
                    ${isPositive ? "+" : ""}${change.toFixed(2)}%
                  </div>
                </div>
              </div>
            `;
          })}
        </div>
      </ha-card>
    `;
  }

  getCardSize() {
    return (this._config?.entities?.length || 3) + 1;
  }

  static getConfigElement() {
    return document.createElement("miruboard-crypto-card-editor");
  }

  static getStubConfig() {
    return { entities: [], title: "Crypto" };
  }
}

// ============================================================
// MIRUBOARD TRAVEL TIME CARD
// ============================================================
class MiruboardTravelCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      _config: { type: Object },
    };
  }

  setConfig(config) {
    if (!config.entities || !config.entities.length) {
      throw new Error("Please define travel time entities");
    }
    this._config = {
      title: "Reistijden",
      ...config,
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      ha-card {
        padding: 16px;
        background: var(--card-background-color);
      }
      .header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 500;
        color: var(--secondary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .header ha-icon {
        --mdc-icon-size: 18px;
      }
      .routes {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .route {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px;
        border-radius: 12px;
        background: var(--primary-background-color);
      }
      .route-left {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .route-name {
        font-weight: 600;
        font-size: 14px;
        color: var(--primary-text-color);
      }
      .route-detail {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      .route-right {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .route-duration {
        font-weight: 700;
        font-size: 20px;
        color: var(--primary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .route-unit {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      .traffic-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
      }
      .traffic-dot.green {
        background: #22c55e;
        box-shadow: 0 0 6px rgba(34, 197, 94, 0.4);
      }
      .traffic-dot.red {
        background: #ef4444;
        box-shadow: 0 0 6px rgba(239, 68, 68, 0.4);
      }
    `;
  }

  render() {
    if (!this.hass || !this._config) return html``;

    return html`
      <ha-card>
        <div class="header">
          <ha-icon icon="mdi:car-clock"></ha-icon>
          ${this._config.title}
        </div>
        <div class="routes">
          ${(this._config.entities || []).map((entityId) => {
            const state = this.hass.states[entityId];
            if (!state) return html``;

            const duration = parseInt(state.state) || 0;
            const traffic = state.attributes.traffic || "unknown";
            const dest = state.attributes.destination || "";
            const name =
              state.attributes.friendly_name?.replace("Miruboard ", "") ||
              entityId;

            return html`
              <div class="route">
                <div class="route-left">
                  <div class="route-name">${name}</div>
                  <div class="route-detail">${dest}</div>
                </div>
                <div class="route-right">
                  <div class="traffic-dot ${traffic}"></div>
                  <div>
                    <span class="route-duration">${duration}</span>
                    <span class="route-unit">min</span>
                  </div>
                </div>
              </div>
            `;
          })}
        </div>
      </ha-card>
    `;
  }

  getCardSize() {
    return (this._config?.entities?.length || 2) + 1;
  }

  static getStubConfig() {
    return { entities: [], title: "Reistijden" };
  }
}

// ============================================================
// MIRUBOARD RSS CARD
// ============================================================
class MiruboardRssCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      _config: { type: Object },
      _currentIndex: { type: Number },
    };
  }

  constructor() {
    super();
    this._currentIndex = 0;
    this._interval = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an RSS entity");
    }
    this._config = {
      title: "Nieuws",
      rotate_seconds: 15,
      max_items: 5,
      ...config,
    };
  }

  connectedCallback() {
    super.connectedCallback();
    this._startRotation();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._stopRotation();
  }

  _startRotation() {
    this._stopRotation();
    const interval = (this._config?.rotate_seconds || 15) * 1000;
    this._interval = setInterval(() => {
      const state = this.hass?.states[this._config?.entity];
      const items = state?.attributes?.items || [];
      if (items.length > 0) {
        this._currentIndex = (this._currentIndex + 1) % items.length;
        this.requestUpdate();
      }
    }, interval);
  }

  _stopRotation() {
    if (this._interval) {
      clearInterval(this._interval);
      this._interval = null;
    }
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      ha-card {
        padding: 16px;
        background: var(--card-background-color);
        overflow: hidden;
      }
      .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }
      .header-left {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 500;
        color: var(--secondary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .header-left ha-icon {
        --mdc-icon-size: 18px;
      }
      .dots {
        display: flex;
        gap: 4px;
      }
      .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--disabled-text-color);
        transition: background 0.3s;
      }
      .dot.active {
        background: var(--primary-color);
      }
      .article {
        animation: fadeIn 0.4s ease;
      }
      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(4px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      .article-source {
        font-size: 11px;
        color: var(--primary-color);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 4px;
      }
      .article-title {
        font-size: 16px;
        font-weight: 700;
        color: var(--primary-text-color);
        line-height: 1.3;
        margin-bottom: 6px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      .article-summary {
        font-size: 13px;
        color: var(--secondary-text-color);
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      .article-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
        font-size: 11px;
        color: var(--disabled-text-color);
      }
      .no-news {
        color: var(--secondary-text-color);
        font-style: italic;
        padding: 16px 0;
        text-align: center;
      }
    `;
  }

  render() {
    if (!this.hass || !this._config) return html``;

    const state = this.hass.states[this._config.entity];
    if (!state) return html`<ha-card>Entity not found</ha-card>`;

    const items = state.attributes.items || [];
    const maxItems = Math.min(items.length, this._config.max_items || 5);
    const visibleItems = items.slice(0, maxItems);

    if (visibleItems.length === 0) {
      return html`
        <ha-card>
          <div class="header">
            <div class="header-left">
              <ha-icon icon="mdi:rss"></ha-icon>
              ${this._config.title}
            </div>
          </div>
          <div class="no-news">Geen nieuws beschikbaar</div>
        </ha-card>
      `;
    }

    const currentItem =
      visibleItems[this._currentIndex % visibleItems.length] || {};

    // Strip HTML tags from summary
    const cleanSummary = (currentItem.summary || "")
      .replace(/<[^>]*>/g, "")
      .substring(0, 200);

    return html`
      <ha-card>
        <div class="header">
          <div class="header-left">
            <ha-icon icon="mdi:rss"></ha-icon>
            ${this._config.title}
          </div>
          <div class="dots">
            ${visibleItems.map(
              (_, i) =>
                html`<div
                  class="dot ${i === this._currentIndex % visibleItems.length
                    ? "active"
                    : ""}"
                ></div>`
            )}
          </div>
        </div>
        <div class="article" key="${this._currentIndex}">
          <div class="article-source">${currentItem.source || "RSS"}</div>
          <div class="article-title">${currentItem.title || "No title"}</div>
          <div class="article-summary">${cleanSummary}</div>
          <div class="article-meta">
            ${currentItem.published
              ? html`<span
                  >${new Date(currentItem.published).toLocaleDateString(
                    "nl-NL"
                  )}</span
                >`
              : ""}
          </div>
        </div>
      </ha-card>
    `;
  }

  getCardSize() {
    return 3;
  }

  static getStubConfig() {
    return { entity: "", title: "Nieuws", rotate_seconds: 15, max_items: 5 };
  }
}

// ============================================================
// MIRUBOARD COMBINED DASHBOARD CARD
// ============================================================
class MiruboardDashboardCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      _config: { type: Object },
    };
  }

  setConfig(config) {
    this._config = {
      title: "Miruboard",
      ...config,
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      ha-card {
        padding: 16px;
        background: var(--card-background-color);
      }
      .dashboard-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--divider-color);
      }
      .dashboard-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--primary-text-color);
      }
      .dashboard-subtitle {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 12px;
      }
      .widget {
        padding: 14px;
        border-radius: 12px;
        background: var(--primary-background-color);
      }
      .widget-header {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 10px;
        font-size: 12px;
        font-weight: 600;
        color: var(--secondary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.4px;
      }
      .widget-header ha-icon {
        --mdc-icon-size: 16px;
      }
    `;
  }

  render() {
    if (!this.hass || !this._config) return html``;

    const now = new Date();
    const timeStr = now.toLocaleTimeString("nl-NL", {
      hour: "2-digit",
      minute: "2-digit",
    });
    const dateStr = now.toLocaleDateString("nl-NL", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });

    return html`
      <ha-card>
        <div class="dashboard-header">
          <div>
            <div class="dashboard-title">${this._config.title}</div>
            <div class="dashboard-subtitle">${dateStr} &middot; ${timeStr}</div>
          </div>
        </div>
        <div class="grid">
          ${this._config.crypto_entities?.length
            ? html`<div class="widget">${this._renderCrypto()}</div>`
            : ""}
          ${this._config.travel_entities?.length
            ? html`<div class="widget">${this._renderTravel()}</div>`
            : ""}
          ${this._config.rss_entity
            ? html`<div class="widget">${this._renderRss()}</div>`
            : ""}
        </div>
      </ha-card>
    `;
  }

  _renderCrypto() {
    return html`
      <div class="widget-header">
        <ha-icon icon="mdi:chart-line"></ha-icon> Crypto
      </div>
      ${(this._config.crypto_entities || []).map((entityId) => {
        const state = this.hass.states[entityId];
        if (!state) return html``;
        const price = parseFloat(state.state) || 0;
        const change = state.attributes.change_24h || 0;
        const name =
          state.attributes.friendly_name?.replace("Miruboard ", "") || entityId;
        const isPos = change >= 0;
        const formatted =
          price >= 1
            ? `€${price.toLocaleString("nl-NL", { minimumFractionDigits: 2 })}`
            : `€${price.toFixed(4)}`;
        return html`
          <div
            style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--divider-color)"
          >
            <span style="font-weight:600;font-size:13px">${name}</span>
            <span>
              <span style="font-weight:700;font-size:13px">${formatted}</span>
              <span
                style="font-size:11px;margin-left:6px;color:${isPos
                  ? "#22c55e"
                  : "#ef4444"}"
              >
                ${isPos ? "+" : ""}${change.toFixed(2)}%
              </span>
            </span>
          </div>
        `;
      })}
    `;
  }

  _renderTravel() {
    return html`
      <div class="widget-header">
        <ha-icon icon="mdi:car-clock"></ha-icon> Reistijden
      </div>
      ${(this._config.travel_entities || []).map((entityId) => {
        const state = this.hass.states[entityId];
        if (!state) return html``;
        const duration = parseInt(state.state) || 0;
        const traffic = state.attributes.traffic || "unknown";
        const name =
          state.attributes.friendly_name?.replace("Miruboard ", "") || entityId;
        const dotColor = traffic === "green" ? "#22c55e" : "#ef4444";
        return html`
          <div
            style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--divider-color)"
          >
            <span style="font-weight:600;font-size:13px">${name}</span>
            <span style="display:flex;align-items:center;gap:8px">
              <span
                style="width:8px;height:8px;border-radius:50%;background:${dotColor}"
              ></span>
              <span style="font-weight:700;font-size:16px">${duration}</span>
              <span style="font-size:11px;color:var(--secondary-text-color)"
                >min</span
              >
            </span>
          </div>
        `;
      })}
    `;
  }

  _renderRss() {
    const state = this.hass.states[this._config.rss_entity];
    if (!state) return html``;
    const items = (state.attributes.items || []).slice(0, 3);
    return html`
      <div class="widget-header">
        <ha-icon icon="mdi:rss"></ha-icon> Nieuws
      </div>
      ${items.map(
        (item) => html`
          <div style="padding:6px 0;border-bottom:1px solid var(--divider-color)">
            <div
              style="font-size:11px;color:var(--primary-color);font-weight:600;text-transform:uppercase"
            >
              ${item.source || "RSS"}
            </div>
            <div
              style="font-size:13px;font-weight:600;color:var(--primary-text-color);margin-top:2px"
            >
              ${item.title}
            </div>
          </div>
        `
      )}
    `;
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return {
      title: "Miruboard",
      crypto_entities: [],
      travel_entities: [],
      rss_entity: "",
    };
  }
}

// ============================================================
// REGISTER ALL CARDS
// ============================================================
customElements.define("miruboard-crypto-card", MiruboardCryptoCard);
customElements.define("miruboard-travel-card", MiruboardTravelCard);
customElements.define("miruboard-rss-card", MiruboardRssCard);
customElements.define("miruboard-dashboard-card", MiruboardDashboardCard);

// Register with HA card picker
window.customCards = window.customCards || [];
window.customCards.push(
  {
    type: "miruboard-crypto-card",
    name: "Miruboard Crypto",
    description: "Cryptocurrency prices with 24h change indicator",
    preview: true,
  },
  {
    type: "miruboard-travel-card",
    name: "Miruboard Reistijden",
    description: "Travel time routes with traffic indicators",
    preview: true,
  },
  {
    type: "miruboard-rss-card",
    name: "Miruboard Nieuws",
    description: "RSS news feed with auto-rotation",
    preview: true,
  },
  {
    type: "miruboard-dashboard-card",
    name: "Miruboard Dashboard",
    description: "Combined dashboard with crypto, travel, and news",
    preview: true,
  }
);

console.info(
  "%c MIRUBOARD %c v1.0.0 ",
  "color: white; background: #6366f1; font-weight: 700; padding: 2px 6px; border-radius: 4px 0 0 4px;",
  "color: #6366f1; background: #e0e7ff; font-weight: 700; padding: 2px 6px; border-radius: 0 4px 4px 0;"
);
