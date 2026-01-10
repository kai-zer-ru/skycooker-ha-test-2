import { LitElement, html, CSSResultGroup, css } from 'lit';
import { property, customElement } from 'lit/decorators.js';
import { HomeAssistant, SkyCookerCardConfig } from './types';

@customElement('skycooker-card')
export class SkyCookerCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;

  @property({ type: String }) public statusEntity?: string;
  @property({ type: String }) public temperatureEntity?: string;
  @property({ type: String }) public remainingTimeEntity?: string;
  @property({ type: String }) public totalTimeEntity?: string;
  @property({ type: String }) public autoWarmTimeEntity?: string;
  @property({ type: String }) public successRateEntity?: string;
  @property({ type: String }) public delayedLaunchTimeEntity?: string;
  @property({ type: String }) public currentModeEntity?: string;

  @property({ type: Boolean }) public showControls = false;

  render() {
    const status = this.getEntityState(this.statusEntity);
    const temperature = this.getEntityState(this.temperatureEntity);
    const remainingTime = this.getEntityState(this.remainingTimeEntity);
    const totalTime = this.getEntityState(this.totalTimeEntity);
    const autoWarmTime = this.getEntityState(this.autoWarmTimeEntity);
    const successRate = this.getEntityState(this.successRateEntity);
    const delayedLaunchTime = this.getEntityState(this.delayedLaunchTimeEntity);
    const currentMode = this.getEntityState(this.currentModeEntity);

    return html`
      <ha-card>
        <div class="card-header">
          <h1>SkyCooker</h1>
          <div class="status-indicator"></div>
        </div>
        <div class="card-content">
          <div class="current-mode">
            <span class="mode-label">Текущий режим:</span>
            <span class="mode-value">${currentMode || 'Ожидание'}</span>
          </div>
          <div class="current-temperature">
            <span class="temp-label">Температура:</span>
            <span class="temp-value">${temperature || '0'}°C</span>
          </div>
          <div class="time-info">
            <span class="time-label">Оставшееся время:</span>
            <span class="time-value">${remainingTime || '0'} мин</span>
          </div>
          <div class="time-info">
            <span class="time-label">Общее время:</span>
            <span class="time-value">${totalTime || '0'} мин</span>
          </div>
          <div class="time-info">
            <span class="time-label">Время автоподогрева:</span>
            <span class="time-value">${autoWarmTime || '0'} мин</span>
          </div>
          <div class="time-info">
            <span class="time-label">Процент успеха:</span>
            <span class="time-value">${successRate || '0'}%</span>
          </div>
          <div class="time-info">
            <span class="time-label">Отложенный запуск:</span>
            <span class="time-value">${delayedLaunchTime || '0'} мин</span>
          </div>
          <div class="controls" ?hidden="${!this.showControls}">
            <button class="control-button" @click="${this.togglePower}">
              <ha-icon icon="mdi:power"></ha-icon>
            </button>
            <button class="control-button" @click="${this.startCooking}">
              <ha-icon icon="mdi:play"></ha-icon>
            </button>
            <button class="control-button" @click="${this.stopCooking}">
              <ha-icon icon="mdi:stop"></ha-icon>
            </button>
          </div>
          <button class="toggle-controls" @click="${this.toggleControls}">
            ${this.showControls ? 'Скрыть управление' : 'Показать управление'}
          </button>
        </div>
      </ha-card>
    `;
  }

  getEntityState(entityId?: string): string | undefined {
    if (!entityId || !this.hass || !this.hass.states) {
      return undefined;
    }
    const entity = this.hass.states[entityId];
    return entity ? entity.state : undefined;
  }

  togglePower() {
    // Логика включения/выключения мультиварки
    console.log('Переключение питания');
  }

  startCooking() {
    // Логика начала приготовления
    console.log('Начало приготовления');
  }

  stopCooking() {
    // Логика остановки приготовления
    console.log('Остановка приготовления');
  }

  toggleControls() {
    this.showControls = !this.showControls;
    this.requestUpdate();
  }

  static get styles(): CSSResultGroup {
    return css`
      ha-card {
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
      }
      .card-header {
        background: linear-gradient(135deg, #4a6bff 0%, #3a5bef 100%);
        color: white;
        padding: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .card-header h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 500;
      }
      .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #ffcc00;
        box-shadow: 0 0 8px rgba(255, 204, 0, 0.5);
      }
      .card-content {
        padding: 16px;
      }
      .current-mode, .current-temperature, .time-info {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #e0e0e0;
      }
      .mode-label, .temp-label, .time-label {
        font-weight: 500;
        color: #555;
      }
      .mode-value, .temp-value, .time-value {
        font-weight: 600;
        color: #333;
      }
      .controls {
        display: flex;
        justify-content: space-around;
        margin: 16px 0;
      }
      .control-button {
        background: linear-gradient(135deg, #4a6bff 0%, #3a5bef 100%);
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s, box-shadow 0.2s;
      }
      .control-button:active {
        transform: scale(0.95);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
      .toggle-controls {
        background: linear-gradient(135deg, #4a6bff 0%, #3a5bef 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 8px 16px;
        cursor: pointer;
        width: 100%;
        margin-top: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s, box-shadow 0.2s;
      }
      .toggle-controls:active {
        transform: scale(0.98);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
    `;
  }
}